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
    "evaluation_policy": (
        SCHEMA_DIR / "part-b-closed-loop-evaluation-policy.schema.json"
    ),
    "episode": SCHEMA_DIR / "part-b-closed-loop-episode.schema.json",
    "feedback": (
        SCHEMA_DIR / "part-b-closed-loop-feedback-envelope.schema.json"
    ),
    "preregistration": (
        SCHEMA_DIR / "part-b-closed-loop-preregistration.schema.json"
    ),
    "manifest": SCHEMA_DIR / "part-b-b6-manifest.schema.json",
}
CONFIG_PATHS = {
    "evaluation_policy": (
        CONFIG_DIR / "part-b-closed-loop-evaluation-policy-v0.8.yaml"
    ),
    "episode": (
        CONFIG_DIR / "part-b-closed-loop-episode-example-v0.8.yaml"
    ),
    "feedback": (
        CONFIG_DIR / "part-b-closed-loop-feedback-example-v0.8.yaml"
    ),
    "preregistration": (
        CONFIG_DIR / "part-b-closed-loop-preregistration-v0.8.yaml"
    ),
    "manifest": CONFIG_DIR / "part-b-b6-manifest-v0.8.yaml",
}
DOCUMENT_PATHS = (
    ROOT / "contracts" / "part-b-b6-boundary-v0.8.md",
    ROOT / "contracts" / "part-b-b6-closed-loop-evaluation-v0.8.md",
    ROOT
    / "contracts"
    / "part-b-b6-preregistration-envelope-v0.8.md",
    ROOT / "src" / "scope" / "part-b-b6-spec-issues.md",
    ROOT
    / "08-writing"
    / "part-b-b6-implementation-plan-v0.8-20260723.md",
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

FROZEN_B2_B5_HASHES = {
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
    "part-b-planner-public-state-example-v0.8.yaml": (
        "sha256:42efd17661a1335f3c84c2c4efbea4de8107087d099dc987a902d20ded50deae"
    ),
    "part-b-planner-decision-example-v0.8.yaml": (
        "sha256:144cd24c0d6e3906ee31d25cdcc629f20901648d58204ee030f397daca23da6d"
    ),
    "part-b-planner-interface-policy-v0.8.yaml": (
        "sha256:b0c9f9971d13efcfeabb39f829592b9502831ba1b94e8de54e3941ba7dd1c343"
    ),
    "part-b-bounded-evaluation-v0.8.yaml": (
        "sha256:9c1cae4643b95f7e2c87b6398cd096db1836ca3533cca67a1842dd037ec66858"
    ),
    "part-b-b5-manifest-v0.8.yaml": (
        "sha256:bbe8bde7e6ab4695fc6a03233a8c45f5d205c77b3bed6f2816a89c8f7616c069"
    ),
}
EXPECTED_BINDING_KEYS = {
    "part-b-stochastic-observation-catalog-v0.8.yaml": (
        "b2_stochastic_catalog_hash"
    ),
    "part-b-stochastic-tv-policy-v0.8.yaml": "b2_tv_policy_hash",
    "part-b-b2-manifest-v0.8.yaml": "b2_manifest_hash",
    "part-b-b2-world-pair-delta-decision-v0.8.yaml": (
        "b2_world_pair_delta_decision_hash"
    ),
    "part-b-cost-instrumentation-policy-v0.8.yaml": (
        "b3_cost_instrumentation_policy_hash"
    ),
    "part-b-b3-manifest-v0.8.yaml": "b3_manifest_hash",
    "part-b-baseline-preregistration-v0.8.yaml": (
        "b4_baseline_preregistration_hash"
    ),
    "part-b-baseline-isolation-policy-v0.8.yaml": (
        "b4_baseline_isolation_policy_hash"
    ),
    "part-b-b4-manifest-v0.8.yaml": "b4_manifest_hash",
    "part-b-planner-public-state-example-v0.8.yaml": (
        "b5_planner_public_state_example_hash"
    ),
    "part-b-planner-decision-example-v0.8.yaml": (
        "b5_planner_decision_example_hash"
    ),
    "part-b-planner-interface-policy-v0.8.yaml": (
        "b5_planner_interface_policy_hash"
    ),
    "part-b-bounded-evaluation-v0.8.yaml": (
        "b5_bounded_evaluation_hash"
    ),
    "part-b-b5-manifest-v0.8.yaml": "b5_manifest_hash",
}


def require_file(path: Path) -> Path:
    if not path.is_file():
        raise AssertionError(
            f"missing approved B6 artifact: {path.relative_to(ROOT)}"
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


class PartBB6ContractTests(unittest.TestCase):
    def test_red_01_required_b6_artifacts_exist(self) -> None:
        """RED-01: the exact sixteen non-test B6 artifacts are mandatory."""
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
            "missing approved B6 artifacts: " + ", ".join(missing),
        )

    def test_red_02_schemas_are_closed_draft_2020_12_contracts(self) -> None:
        """RED-02: every B6 schema rejects undeclared authority fields."""
        for name, path in SCHEMA_PATHS.items():
            schema = load_json(path)
            with self.subTest(schema=name):
                self.assertEqual(
                    schema["$schema"],
                    "https://json-schema.org/draft/2020-12/schema",
                )
                self.assertIs(schema.get("additionalProperties"), False)
                Draft202012Validator.check_schema(schema)

    def test_red_03_configs_validate_and_unknown_fields_fail_closed(self) -> None:
        """RED-03: every example validates and unknown fields are rejected."""
        schemas = {
            name: load_json(path) for name, path in SCHEMA_PATHS.items()
        }
        configs = {
            name: load_yaml(path) for name, path in CONFIG_PATHS.items()
        }
        for name, config in configs.items():
            with self.subTest(config=name):
                self.assertEqual(validate(config, schemas[name]), [])
                unknown = deepcopy(config)
                unknown["unexpected_execution_authority"] = True
                self.assertTrue(validate(unknown, schemas[name]))

    def test_red_04_b6_canonical_hashes_replay_and_tampering_is_visible(
        self,
    ) -> None:
        """RED-04: every new config is self-bound by canonical hash."""
        schemas = {
            name: load_json(path) for name, path in SCHEMA_PATHS.items()
        }
        for name, path in CONFIG_PATHS.items():
            config = load_yaml(path)
            with self.subTest(config=name):
                self.assertEqual(
                    config["hash"],
                    canonical_document_hash(config),
                )
                missing = deepcopy(config)
                missing.pop("hash")
                self.assertTrue(validate(missing, schemas[name]))
                tampered = deepcopy(config)
                tampered["hash"] = "sha256:" + ("0" * 64)
                self.assertNotEqual(
                    tampered["hash"],
                    canonical_document_hash(tampered),
                )

    def test_red_05_b2_b5_bindings_are_exact_and_read_only(self) -> None:
        """RED-05: B6 replays every frozen B2-B5 identity exactly."""
        manifest = load_yaml(CONFIG_PATHS["manifest"])
        bindings = manifest["bindings"]
        self.assertEqual(
            set(bindings),
            set(EXPECTED_BINDING_KEYS.values()),
        )
        for filename, expected_hash in FROZEN_B2_B5_HASHES.items():
            with self.subTest(filename=filename):
                inherited = load_yaml(CONFIG_DIR / filename)
                self.assertEqual(inherited["hash"], expected_hash)
                self.assertEqual(
                    bindings[EXPECTED_BINDING_KEYS[filename]],
                    expected_hash,
                )

    def test_red_06_manifest_grants_contract_authority_only(self) -> None:
        """RED-06: opening B6 does not open any execution authority."""
        manifest = load_yaml(CONFIG_PATHS["manifest"])
        self.assertEqual(manifest["status"], "B6_CONTRACT_ONLY")
        self.assertEqual(
            manifest["authorized_slice"],
            "B6_CLOSED_LOOP_EVAL",
        )
        self.assertIs(manifest["closed_loop_contract_authority"], True)
        self.assertIs(
            manifest["preregistration_contract_authority"],
            True,
        )
        for field in (
            "planner_implementation_admission_authority",
            "planner_execution_authority",
            "evaluation_execution_authority",
            "sampling_authority",
            "production_capture_authority",
            "connector_authority",
            "scalarization_authority",
            "performance_claim_authority",
        ):
            with self.subTest(authority=field):
                self.assertIs(manifest[field], False)
        self.assertEqual(manifest["stop_authority"], "NONE")
        self.assertEqual(manifest["llm_integration"], "FORBIDDEN")
        self.assertEqual(manifest["closed_slices"], ["B7", "B8", "B9"])

    def test_red_07_b4_roster_is_replayed_without_new_methods(self) -> None:
        """RED-07: B6 cannot add or rename a preregistered method."""
        policy = load_yaml(CONFIG_PATHS["evaluation_policy"])
        b4 = load_yaml(
            CONFIG_DIR / "part-b-baseline-preregistration-v0.8.yaml"
        )
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

    def test_red_08_control_and_oracle_roles_cannot_be_laundered(self) -> None:
        """RED-08: B4 evaluator/control roles stay non-deployable."""
        policy = load_yaml(CONFIG_PATHS["evaluation_policy"])
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
        public_ids = policy["b4_roster_binding"][
            "public_action_selector_ids"
        ]
        self.assertNotIn("ORACLE_EVALUATION_ONLY", public_ids)
        self.assertNotIn("NO_ACQUISITION", public_ids)

    def test_red_09_b4_partition_isolation_is_unchanged(self) -> None:
        """RED-09: TRAIN/TUNE/EVALUATION/HOLDOUT remain isolated."""
        preregistration = load_yaml(CONFIG_PATHS["preregistration"])
        isolation = preregistration["isolation_binding"]
        self.assertEqual(
            isolation["partitions"],
            ["TRAIN", "TUNE", "EVALUATION", "HOLDOUT"],
        )
        self.assertIs(isolation["mutually_disjoint"], True)
        self.assertIs(isolation["evaluation_feedback_to_train"], False)
        self.assertIs(isolation["evaluation_feedback_to_tune"], False)
        self.assertIs(isolation["holdout_visible_before_final_freeze"], False)
        self.assertIs(isolation["holdout_feedback_to_any_model"], False)
        self.assertEqual(
            isolation["forbidden_path_prefixes"],
            ["09-experiments/"],
        )

    def test_red_10_preregistration_freezes_before_first_feedback(self) -> None:
        """RED-10: no post-outcome roster, metric or policy mutation."""
        preregistration = load_yaml(CONFIG_PATHS["preregistration"])
        freeze = preregistration["freeze_rules"]
        self.assertEqual(freeze["freeze_point"], "BEFORE_FIRST_FEEDBACK")
        self.assertIs(freeze["must_precede_first_feedback"], True)
        for field in (
            "roster_mutation_after_freeze",
            "artifact_hash_mutation_after_freeze",
            "metric_mutation_after_freeze",
            "partition_mutation_after_freeze",
            "bound_mutation_after_freeze",
            "tie_break_mutation_after_freeze",
        ):
            with self.subTest(field=field):
                self.assertIs(freeze[field], False)
        self.assertEqual(
            freeze["violation_behavior"],
            "FAIL_CLOSED_EVALUATION_NOT_PREREGISTERED",
        )

    def test_red_11_pb_b5_si_001_remains_open(self) -> None:
        """RED-11: B6 contracts do not admit legacy or new Planners."""
        b6_issues = require_file(
            ROOT / "src" / "scope" / "part-b-b6-spec-issues.md"
        ).read_text(encoding="utf-8")
        boundary = require_file(
            ROOT / "contracts" / "part-b-b6-boundary-v0.8.md"
        ).read_text(encoding="utf-8")
        b5_issues = require_file(
            ROOT / "src" / "scope" / "part-b-b5-spec-issues.md"
        ).read_text(encoding="utf-8")
        corpus = "\n".join((b6_issues, boundary, b5_issues))
        for token in (
            "PB-B5-SI-001",
            "OPEN",
            "BLOCKS IMPLEMENTATION ADMISSION AND EXECUTION",
            "Legacy M3* implementation admission: NOT ESTABLISHED",
            "Legacy M3* execution authority: NONE",
            "UNCHANGED_OPEN_FROM_B5",
        ):
            with self.subTest(token=token):
                self.assertIn(token, corpus)

    def test_red_12_configs_contain_no_runtime_or_retrieval_material(
        self,
    ) -> None:
        """RED-12: contract examples cannot smuggle runtime locators."""
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


if __name__ == "__main__":
    unittest.main()
