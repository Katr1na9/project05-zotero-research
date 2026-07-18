import gzip
import hashlib
import importlib.util
import json
import re
import unittest
from pathlib import Path


EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
WP2_ROOT = EXPERIMENT_ROOT / "llm_evidence_compiler_mainline" / "generated" / "wp2"
PUBLIC_ROOT = WP2_ROOT / "public"
PRIVATE_ROOT = WP2_ROOT / "private"
RULE_ROOT = WP2_ROOT / "rule-strong-development"
CANONICAL_CLAIM_ID = re.compile(r"\bC[0-9]{2}-EC-[0-9]{3}\b")


def load_script(name: str):
    path = EXPERIMENT_ROOT / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


builder = load_script("build_compiler_public_request")
wp2_builder = load_script("build_compiler_wp2_data")
rule = load_script("run_compiler_rule_strong")


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl_gz(path: Path):
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


class WP2DataReadinessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = load_json(WP2_ROOT / "data-readiness.json")
        cls.artifacts = read_jsonl_gz(PUBLIC_ROOT / "artifact_records.jsonl.gz")
        cls.artifact_catalog = load_json(PUBLIC_ROOT / "artifact_catalog.json")
        cls.target_catalog = load_json(PUBLIC_ROOT / "target_node_catalog.json")
        cls.visibility = load_json(PUBLIC_ROOT / "visibility_scenarios.json")
        cls.private_reference = load_json(PRIVATE_ROOT / "reference_map.json")
        cls.private_execution = load_json(PRIVATE_ROOT / "execution_visibility.json")

    def test_all_nine_cases_and_fifty_eight_pointers_are_ready(self):
        self.assertEqual("passed_pointer_resolution_with_surface_diagnostics", self.report["status"])
        self.assertEqual(9, self.report["case_count"])
        self.assertEqual(3, self.report["development_case_count"])
        self.assertEqual(6, self.report["test_case_count"])
        self.assertEqual(58, self.report["frozen_reference_claim_count"])
        self.assertEqual(58, self.report["resolved_pointer_count"])
        self.assertEqual(58, len(self.artifacts))
        self.assertEqual(58, len({row["artifact_id"] for row in self.artifacts}))

    def test_public_artifact_and_record_hashes_are_self_consistent(self):
        catalog_ids = {
            row["artifact_id"] for row in self.artifact_catalog["artifacts"]
        }
        self.assertEqual(catalog_ids, {row["artifact_id"] for row in self.artifacts})
        for artifact in self.artifacts:
            with self.subTest(artifact=artifact["artifact_id"]):
                core = {
                    key: value
                    for key, value in artifact.items()
                    if key != "artifact_sha256"
                }
                self.assertEqual(
                    artifact["artifact_sha256"], builder.sha256_value(core)
                )
                for record in artifact["records"]:
                    self.assertEqual(
                        record["record_sha256"],
                        builder.sha256_value(record["payload"]),
                    )

    def test_public_package_contains_no_canonical_claim_or_oracle_fields(self):
        public_values = [
            self.artifact_catalog,
            self.target_catalog,
            self.visibility,
            *self.artifacts,
        ]
        for value in public_values:
            with self.subTest(value_type=type(value).__name__):
                builder.assert_public_boundary(value)
                self.assertIsNone(
                    CANONICAL_CLAIM_ID.search(builder.canonical_json_text(value))
                )
        self.assertFalse(self.report["public_contract_reference_fields_used"])
        self.assertEqual("passed", self.report["public_private_scan"]["status"])
        self.assertEqual([], self.report["public_private_scan"]["private_identifier_collisions"])

    def test_target_contracts_use_reference_free_public_stage_vocabulary(self):
        for case in self.target_catalog["cases"]:
            self.assertEqual(
                "frozen_public_stage_vocabulary_v0.1_without_reference_claims",
                case["stage_a_target_contract"],
            )
            for node in case["nodes"]:
                self.assertTrue(node["allowed_claim_types"])
                self.assertTrue(node["allowed_predicates"])
                self.assertNotIn("required_claim_ids", node)
        claim_types, predicates = wp2_builder.public_target_contract("actor_attribution")
        self.assertEqual(["other"], claim_types)
        self.assertEqual(["unsupported_by_local_observation"], predicates)

    def test_public_scenarios_hide_mask_seed_and_future_outcomes(self):
        self.assertEqual(405, len(self.visibility["scenarios"]))
        self.assertFalse(self.visibility["mask_metadata_visible"])
        self.assertFalse(self.visibility["future_action_outcomes_visible"])
        forbidden = {"mask_strategy", "mask_intensity", "random_seed", "hidden_claim_ids"}
        for scenario in self.visibility["scenarios"]:
            self.assertFalse(forbidden.intersection(scenario))

    def test_private_action_revelations_reference_existing_public_artifacts(self):
        public_ids = {artifact["artifact_id"] for artifact in self.artifacts}
        action_count = 0
        for case in self.private_execution["cases"]:
            for action in case["actions"]:
                action_count += 1
                self.assertLessEqual(
                    set(action["reveals_artifact_ids_on_success"]), public_ids
                )
        self.assertEqual(50, action_count)


class RuleStrongSnapshotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.snapshot_path = RULE_ROOT / "rule-strong-development-snapshot.json"
        cls.snapshot = load_json(cls.snapshot_path)
        cls.results = load_json(RULE_ROOT / "rule-results.json")
        cls.requests = read_jsonl_gz(RULE_ROOT / "public-requests.jsonl.gz")

    def test_rule_snapshot_is_development_only_and_pre_model(self):
        self.assertEqual("frozen_before_any_llm_output", self.snapshot["status"])
        self.assertEqual("development", self.snapshot["split"])
        self.assertEqual(
            [
                "C04-compiler-evaluation",
                "C05-compiler-evaluation",
                "C06-compiler-evaluation",
            ],
            self.snapshot["case_ids"],
        )
        self.assertEqual([], self.snapshot["test_case_ids_processed"])
        self.assertTrue(all(request["split"] == "development" for request in self.requests))
        self.assertFalse(self.snapshot["private_files_read"])
        self.assertFalse(self.snapshot["reference_data_used"])
        self.assertFalse(self.snapshot["model_runtime_used"])
        self.assertFalse(self.snapshot["training_used"])

    def test_rule_snapshot_counts_and_admission_are_frozen(self):
        self.assertEqual(3, self.snapshot["case_count"])
        self.assertEqual(26, self.snapshot["artifact_count"])
        self.assertEqual(26, self.snapshot["record_count"])
        self.assertEqual(26, self.snapshot["raw_candidate_count"])
        self.assertEqual(26, self.snapshot["admitted_claim_count"])
        self.assertEqual(15, self.snapshot["admitted_link_count"])
        self.assertEqual(0, self.snapshot["diagnostic_skip_count"])
        self.assertEqual(0, self.snapshot["rejected_candidate_count"])
        self.assertEqual(0, self.snapshot["rejected_link_count"])
        self.assertEqual(
            self.snapshot["results_sha256"],
            builder.sha256_value(self.results),
        )

    def test_snapshot_and_implementation_hashes_match_bytes(self):
        sidecar = (RULE_ROOT / "rule-strong-development-snapshot.sha256").read_text(
            encoding="utf-8"
        ).strip()
        self.assertEqual(sidecar, sha256_file(self.snapshot_path))
        for filename, expected in self.snapshot["implementation_sha256"].items():
            with self.subTest(filename=filename):
                self.assertEqual(
                    expected,
                    sha256_file(EXPERIMENT_ROOT / "scripts" / filename),
                )

    def test_saved_requests_rebuild_from_public_package_byte_equivalently(self):
        rebuilt = rule.build_development_requests(PUBLIC_ROOT)
        self.assertEqual(self.requests, rebuilt)
        self.assertTrue(
            all(not builder.validate_public_request_integrity(request) for request in rebuilt)
        )


if __name__ == "__main__":
    unittest.main()
