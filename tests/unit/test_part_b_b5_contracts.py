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
    "public_state": SCHEMA_DIR / "part-b-planner-public-state.schema.json",
    "decision": SCHEMA_DIR / "part-b-planner-decision.schema.json",
    "interface_policy": (
        SCHEMA_DIR / "part-b-planner-interface-policy.schema.json"
    ),
    "bounded_evaluation": (
        SCHEMA_DIR / "part-b-bounded-evaluation.schema.json"
    ),
    "manifest": SCHEMA_DIR / "part-b-b5-manifest.schema.json",
}
CONFIG_PATHS = {
    "public_state": (
        CONFIG_DIR / "part-b-planner-public-state-example-v0.8.yaml"
    ),
    "decision": (
        CONFIG_DIR / "part-b-planner-decision-example-v0.8.yaml"
    ),
    "interface_policy": (
        CONFIG_DIR / "part-b-planner-interface-policy-v0.8.yaml"
    ),
    "bounded_evaluation": (
        CONFIG_DIR / "part-b-bounded-evaluation-v0.8.yaml"
    ),
    "manifest": CONFIG_DIR / "part-b-b5-manifest-v0.8.yaml",
}
DOCUMENT_PATHS = (
    ROOT / "contracts" / "part-b-b5-boundary-v0.8.md",
    ROOT / "contracts" / "part-b-b5-planner-interface-v0.8.md",
    ROOT / "contracts" / "part-b-b5-bounded-evaluation-v0.8.md",
    ROOT / "src" / "scope" / "part-b-b0-spec-issues.md",
    ROOT / "src" / "scope" / "part-b-b5-spec-issues.md",
    ROOT
    / "08-writing"
    / "part-b-b5-implementation-plan-v0.8-20260723.md",
    ROOT / "08-writing" / "KERNEL-V0.8-AUTHORITY-STATUS-20260722.md",
)

EXPECTED_B4_ROSTER = [
    "NO_ACQUISITION",
    "RANDOM_FEASIBLE",
    "COVERAGE_GREEDY",
    "CMI_PROXY",
    "M1_STATIC_EXPECTED_GAIN",
    "M2_TRANSPARENT",
    "M3A_GAP_COMPATIBILITY",
    "LOGISTIC_M3B",
    "XGBOOST_ACTION_VALUE",
    "AFA_VOI_MYOPIC",
    "AFA_VOI_ROLLOUT_H3",
    "DEPTH2_PUBLIC",
    "ORACLE_EVALUATION_ONLY",
]
EXPECTED_PUBLIC_SELECTOR_IDS = [
    "RANDOM_FEASIBLE",
    "COVERAGE_GREEDY",
    "CMI_PROXY",
    "M1_STATIC_EXPECTED_GAIN",
    "M2_TRANSPARENT",
    "M3A_GAP_COMPATIBILITY",
    "LOGISTIC_M3B",
    "XGBOOST_ACTION_VALUE",
    "AFA_VOI_MYOPIC",
    "AFA_VOI_ROLLOUT_H3",
    "DEPTH2_PUBLIC",
]

FROZEN_ARTIFACT_HASHES = {
    "part-b-observation-contract-v0.8.yaml": (
        "sha256:f5db6035452236fb6e316b8e9a5ada7e2a7cbce07c0eedc3b3e7c890bc4fd7d9"
    ),
    "part-b-cost-contract-v0.8.yaml": (
        "sha256:b6d36c40f7b52c12733dbe75cbcba6058e952f23d67e2155bd73196f6bcfaf53"
    ),
    "part-b-b0-manifest-v0.8.yaml": (
        "sha256:22601f9876ecc8b348a9a2d836b3b842576de4f1442124cb2e82807e30096b4f"
    ),
    "part-b-federation-contract-v0.8.yaml": (
        "sha256:6dd5ddb6b9b7c48b0d93fa8fe0637403596435f766f328895265041467bea23d"
    ),
    "part-b-adapter-conformance-v0.8.yaml": (
        "sha256:f0c3b5fe0a2fa8a1ac9d92a88058223fb12af21bf98f5fe5930d76b662ef7b6a"
    ),
    "part-b-b1-manifest-v0.8.yaml": (
        "sha256:cecc07466d0aec0dbc7b4d95127651546ba7eb895f98a56d7e37c6f753850f6e"
    ),
    "part-b-stochastic-observation-catalog-v0.8.yaml": (
        "sha256:200f0ccd89525bcbda89ea77101cdcab7fda675888938ee106e389a1a8beeab5"
    ),
    "part-b-stochastic-tv-policy-v0.8.yaml": (
        "sha256:b25ed05fdbd9780c1d0de1889e7651220e8a2fc9ce6a86fcdf4720926a31d3e8"
    ),
    "part-b-b2-manifest-v0.8.yaml": (
        "sha256:6d6f67d9722eff1b2e1aa75277b0c390dc485751067728a347ae89c77f83faed"
    ),
    "part-b-b2-world-pair-delta-decision-v0.8.yaml": (
        "sha256:1a9668ef8c968c968e14587778d261b023dff60a0234e4e67251051ec07e5919"
    ),
    "part-b-cost-instrumentation-policy-v0.8.yaml": (
        "sha256:c64865166be067da37a6f4f5d745ce8dc0421dc342d88589c9bbce6142eb3278"
    ),
    "part-b-b3-manifest-v0.8.yaml": (
        "sha256:9403004d25c1428beeb85f04c6d65eeb02759d6881ede67390a2d97f2b9c82fb"
    ),
    "part-b-baseline-preregistration-v0.8.yaml": (
        "sha256:c51ab64588441855a7ff8413e32695e4b168d6d2a2089674f2cdcd691959906d"
    ),
    "part-b-baseline-isolation-policy-v0.8.yaml": (
        "sha256:8e95dd5ae4ae87140de815101b26592e97432dbf64541474b8bcdacb386b5c1f"
    ),
    "part-b-b4-manifest-v0.8.yaml": (
        "sha256:2649b2a9067858d5fe2fa4c2f9d6386408384448910c97ee4eb89f1817893afc"
    ),
}


def require_file(path: Path) -> Path:
    if not path.is_file():
        raise AssertionError(
            f"missing approved B5 artifact: {path.relative_to(ROOT)}"
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


class PartBB5ContractTests(unittest.TestCase):
    def test_red_01_required_b5_artifacts_exist(self) -> None:
        """RED-01: five schemas and five configs are mandatory."""
        for path in (*SCHEMA_PATHS.values(), *CONFIG_PATHS.values()):
            with self.subTest(path=path.relative_to(ROOT)):
                require_file(path)

    def test_red_02_schemas_are_closed_draft_2020_12_contracts(self) -> None:
        """RED-02: unknown fields and authority expansion fail closed."""
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

        for field in (
            "planner_execution_authority",
            "evaluation_execution_authority",
            "sampling_authority",
            "production_capture_authority",
            "scalarization_authority",
            "performance_claim_authority",
        ):
            expanded = deepcopy(configs["manifest"])
            expanded[field] = True
            with self.subTest(authority=field):
                self.assertTrue(validate(expanded, schemas["manifest"]))

        expanded = deepcopy(configs["manifest"])
        expanded["stop_authority"] = "B5_PLANNER"
        self.assertTrue(validate(expanded, schemas["manifest"]))

    def test_red_07_b5_replays_the_exact_b4_roster(self) -> None:
        """RED-07: B5 cannot silently add an approved planner identity."""
        b4 = load_yaml(
            CONFIG_DIR / "part-b-baseline-preregistration-v0.8.yaml"
        )
        policy = load_yaml(CONFIG_PATHS["interface_policy"])
        b4_ids = [row["baseline_id"] for row in b4["baselines"]]
        binding = policy["b4_roster_binding"]

        self.assertEqual(b4_ids, EXPECTED_B4_ROSTER)
        self.assertEqual(binding["all_roster_ids"], b4_ids)
        self.assertEqual(
            binding["public_action_selector_ids"],
            EXPECTED_PUBLIC_SELECTOR_IDS,
        )
        self.assertEqual(
            binding["unregistered_method_behavior"],
            "FAIL_CLOSED_NOT_ADMITTED",
        )
        self.assertEqual(
            set(binding["public_action_selector_ids"]),
            set(b4_ids)
            - {"NO_ACQUISITION", "ORACLE_EVALUATION_ONLY"},
        )

    def test_red_08_oracle_and_no_acquisition_roles_are_preserved(self) -> None:
        """RED-08: evaluator-only and no-action control cannot be laundered."""
        policy = load_yaml(CONFIG_PATHS["interface_policy"])
        roles = policy["role_enforcement"]
        self.assertEqual(
            roles["oracle_evaluation_only"],
            "FORBIDDEN_AS_DEPLOYABLE_PLANNER",
        )
        self.assertEqual(
            roles["no_acquisition"],
            "CONTROL_NO_ACTION_ONLY",
        )
        self.assertIs(roles["b4_role_preservation_required"], True)
        self.assertNotIn(
            "ORACLE_EVALUATION_ONLY",
            policy["b4_roster_binding"]["public_action_selector_ids"],
        )
        self.assertNotIn(
            "NO_ACQUISITION",
            policy["b4_roster_binding"]["public_action_selector_ids"],
        )

    def test_red_09_unverified_legacy_m3star_is_not_admitted(self) -> None:
        """RED-09: interface shape never grants legacy runtime authority."""
        policy = load_yaml(CONFIG_PATHS["interface_policy"])
        admission = policy["implementation_admission"]
        self.assertEqual(admission["approved_implementations"], [])
        self.assertEqual(
            admission["legacy_m3star_status"],
            "NOT_ADMITTED_UNVERIFIED",
        )
        self.assertEqual(
            admission["legacy_runtime_identifiers"],
            ["project05_m3star_h3_dual"],
        )
        self.assertIs(
            admission["shape_compatibility_grants_admission"],
            False,
        )
        self.assertIs(admission["executable_locator_allowed"], False)

    def test_red_10_pb_si_005_has_a_narrow_interface_only_ruling(self) -> None:
        """RED-10: issue closure does not become implementation approval."""
        b0_issues = require_file(
            ROOT / "src" / "scope" / "part-b-b0-spec-issues.md"
        ).read_text(encoding="utf-8")
        b5_issues = require_file(
            ROOT / "src" / "scope" / "part-b-b5-spec-issues.md"
        ).read_text(encoding="utf-8")
        interface_contract = require_file(
            ROOT / "contracts" / "part-b-b5-planner-interface-v0.8.md"
        ).read_text(encoding="utf-8")
        corpus = "\n".join((b0_issues, b5_issues, interface_contract))

        for token in (
            "PB-SI-005",
            "CLOSED — APPROVED FOR B5 INTERFACE CONTRACT ONLY",
            "PB-B5-SI-001",
            "OPEN — BLOCKS IMPLEMENTATION ADMISSION AND EXECUTION",
            "Legacy M3* implementation admission: NOT ESTABLISHED",
            "Legacy M3* execution authority: NONE",
        ):
            with self.subTest(token=token):
                self.assertIn(token, corpus)

    def test_red_14_manifest_has_contract_authority_only(self) -> None:
        """RED-14: B5 can define contracts but cannot execute or claim."""
        manifest = load_yaml(CONFIG_PATHS["manifest"])
        self.assertEqual(manifest["status"], "B5_CONTRACT_ONLY")
        self.assertEqual(
            manifest["authorized_slice"],
            "B5_PLANNER_INTERFACE",
        )
        self.assertIs(manifest["planner_interface_authority"], True)
        self.assertIs(
            manifest["bounded_evaluation_contract_authority"],
            True,
        )
        for field in (
            "planner_execution_authority",
            "evaluation_execution_authority",
            "sampling_authority",
            "production_capture_authority",
            "scalarization_authority",
            "performance_claim_authority",
        ):
            with self.subTest(authority=field):
                self.assertIs(manifest[field], False)
        self.assertEqual(manifest["stop_authority"], "NONE")
        self.assertEqual(manifest["llm_integration"], "FORBIDDEN")
        self.assertEqual(
            manifest["closed_slices"],
            ["B6", "B7", "B8", "B9"],
        )

    def test_red_15_hashes_replay_and_b0_b4_stay_frozen(self) -> None:
        """RED-15: new hashes replay; all inherited hashes remain exact."""
        schemas = {
            name: load_json(path) for name, path in SCHEMA_PATHS.items()
        }
        configs = {
            name: load_yaml(path) for name, path in CONFIG_PATHS.items()
        }

        for name, artifact in configs.items():
            with self.subTest(artifact=name):
                self.assertEqual(
                    artifact["hash"],
                    canonical_document_hash(artifact),
                )
                missing = deepcopy(artifact)
                missing.pop("hash")
                self.assertTrue(validate(missing, schemas[name]))

                wrong = deepcopy(artifact)
                wrong["hash"] = "sha256:" + ("0" * 64)
                self.assertNotEqual(
                    wrong["hash"],
                    canonical_document_hash(wrong),
                )

        for filename, expected_hash in FROZEN_ARTIFACT_HASHES.items():
            with self.subTest(frozen_artifact=filename):
                artifact = load_yaml(CONFIG_DIR / filename)
                self.assertEqual(artifact["hash"], expected_hash)

        manifest = configs["manifest"]
        self.assertEqual(
            manifest["bindings"]["b4_baseline_preregistration_hash"],
            FROZEN_ARTIFACT_HASHES[
                "part-b-baseline-preregistration-v0.8.yaml"
            ],
        )
        self.assertEqual(
            manifest["bindings"]["b4_baseline_isolation_policy_hash"],
            FROZEN_ARTIFACT_HASHES[
                "part-b-baseline-isolation-policy-v0.8.yaml"
            ],
        )
        self.assertEqual(
            manifest["bindings"]["b4_manifest_hash"],
            FROZEN_ARTIFACT_HASHES["part-b-b4-manifest-v0.8.yaml"],
        )
        self.assertEqual(
            manifest["bindings"]["planner_public_state_example_hash"],
            configs["public_state"]["hash"],
        )
        self.assertEqual(
            manifest["bindings"]["planner_decision_example_hash"],
            configs["decision"]["hash"],
        )
        self.assertEqual(
            manifest["bindings"]["planner_interface_policy_hash"],
            configs["interface_policy"]["hash"],
        )
        self.assertEqual(
            manifest["bindings"]["bounded_evaluation_hash"],
            configs["bounded_evaluation"]["hash"],
        )

    def test_red_17_documents_keep_every_runtime_boundary_closed(self) -> None:
        """RED-17: contracts explicitly preserve the forbidden scope."""
        texts = {
            path: require_file(path).read_text(encoding="utf-8")
            for path in DOCUMENT_PATHS
        }
        boundary = texts[
            ROOT / "contracts" / "part-b-b5-boundary-v0.8.md"
        ]
        for token in (
            "B5_PLANNER_INTERFACE",
            "planner_execution_authority=false",
            "evaluation_execution_authority=false",
            "sampling_authority=false",
            "production_capture_authority=false",
            "scalarization_authority=false",
            "performance_claim_authority=false",
            "stop_authority=NONE",
            "NO_BASELINE_EXECUTION",
            "NO_B2_SAMPLER",
            "NO_B3_PRODUCTION_CAPTURE",
            "NO_CONNECTOR",
        ):
            with self.subTest(boundary_token=token):
                self.assertIn(token, boundary)

        corpus = "\n".join(texts.values())
        for token in (
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

    def test_red_18_configs_contain_no_runtime_or_retrieval_material(self) -> None:
        """RED-18: non-executable examples cannot smuggle a runtime."""
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
            "module",
            "module_path",
            "entrypoint",
            "command",
            "executable",
            "model_path",
        }
        forbidden_value_tokens = (
            "http://",
            "https://",
            "curl ",
            "wget ",
            ".py",
        )

        for artifact_name, path in CONFIG_PATHS.items():
            artifact = load_yaml(path)
            for key, value in walk(artifact):
                with self.subTest(artifact=artifact_name, key=key):
                    self.assertNotIn(key.lower(), forbidden_keys)
                if isinstance(value, str):
                    lowered = value.lower()
                    self.assertFalse(
                        any(
                            token in lowered
                            for token in forbidden_value_tokens
                        ),
                        f"{artifact_name} contains runtime material: {value}",
                    )

    def test_red_19_passing_b5_proves_contract_consistency_only(self) -> None:
        """RED-19: no validity or superiority claim follows from B5."""
        corpus = "\n".join(
            require_file(path).read_text(encoding="utf-8")
            for path in DOCUMENT_PATHS
        )
        for token in (
            "CONTRACT_CONSISTENCY_ONLY",
            "NO_IMPLEMENTATION_VALIDATION",
            "NO_PERFORMANCE_VALIDITY",
            "NO_SUPERIORITY_CLAIM",
        ):
            with self.subTest(token=token):
                self.assertIn(token, corpus)


if __name__ == "__main__":
    unittest.main()
