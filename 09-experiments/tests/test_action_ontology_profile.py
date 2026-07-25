import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


EXP = Path(__file__).resolve().parents[1]
SCRIPTS = EXP / "scripts"
EXAMPLES = EXP / "examples"
REAL_CASES = EXP / "real_cases"


def load_script(name):
    path = SCRIPTS / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"test_{name}", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


BUILDER = load_script("build_action_ontology_draft")
VALIDATOR = load_script("validate_action_ontology_profile")


class ActionOntologyProfileTests(unittest.TestCase):
    def build_to(self, path):
        profile = BUILDER.build_profile(
            EXAMPLES,
            REAL_CASES,
            "2026-07-18T00:00:00Z",
        )
        path.write_text(
            json.dumps(profile, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        return profile

    def test_builder_covers_c01_c12_without_mutating_case_actions(self):
        source_paths = sorted(EXAMPLES.glob("C*/acquisition_actions.json")) + sorted(
            REAL_CASES.glob("C*/acquisition_actions.json")
        )
        before = {path: path.read_bytes() for path in source_paths}

        profile = BUILDER.build_profile(
            EXAMPLES,
            REAL_CASES,
            "2026-07-18T00:00:00Z",
        )

        self.assertEqual(12, len(profile["scope"]["case_ids"]))
        self.assertEqual(72, profile["scope"]["action_count"])
        self.assertEqual(41, sum(row["phase"] == "calibration" for row in profile["actions"]))
        self.assertEqual(31, sum(row["phase"] == "development" for row in profile["actions"]))
        self.assertEqual("sealed", profile["data_boundary"]["C13_plus"])
        self.assertEqual(
            "outcome_reveal_simulator",
            profile["runtime_audit"]["current_executor_type"],
        )
        self.assertFalse(
            profile["runtime_audit"]["operational_cost_measurement_eligible"]
        )
        self.assertEqual(before, {path: path.read_bytes() for path in source_paths})

    def test_sidecar_keeps_source_targets_but_excludes_legacy_cost(self):
        profile = BUILDER.build_profile(
            EXAMPLES,
            REAL_CASES,
            "2026-07-18T00:00:00Z",
        )
        target_types = {row["target"]["target_type"] for row in profile["actions"]}

        self.assertTrue(
            {"command", "context", "endpoint", "module", "thread"}.issubset(
                target_types
            )
        )
        self.assertTrue(all("cost" not in row for row in profile["actions"]))
        self.assertTrue(all("cost_breakdown" not in row for row in profile["actions"]))

    def test_counting_semantics_freeze_three_noninterchangeable_counts(self):
        profile = BUILDER.build_profile(
            EXAMPLES,
            REAL_CASES,
            "2026-07-18T00:00:00Z",
        )
        semantics = profile["counting_semantics"]

        self.assertEqual("frozen_v0.1", semantics["status"])
        self.assertTrue(semantics["planner_decision_count"]["stop_counts_as_decision"])
        self.assertFalse(semantics["execution_attempt_count"]["stop_counts_as_attempt"])
        self.assertTrue(semantics["execution_attempt_count"]["retries_are_new_attempts"])
        self.assertTrue(
            semantics["primitive_operation_count"][
                "implicit_one_per_planner_action_forbidden"
            ]
        )
        self.assertEqual(
            {
                "split_equivalent",
                "merge_equivalent",
                "retry_not_mergeable",
                "shared_overhead_conservation",
            },
            set(semantics["split_merge_invariance"]["required_tests"]),
        )

    def test_generated_draft_is_valid_and_source_replayable_but_not_frozen(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "action-ontology.json"
            self.build_to(path)

            report = VALIDATOR.validate_profile(path)

            self.assertTrue(report["schema_valid"])
            self.assertTrue(report["coverage_valid"])
            self.assertTrue(report["source_integrity_valid"])
            self.assertFalse(report["operational_cost_measurement_eligible"])
            self.assertEqual(12, report["case_count"])
            self.assertEqual(72, report["action_count"])
            self.assertGreater(report["unresolved_mapping_count"], 0)
            self.assertFalse(report["formal_ready"])
            self.assertEqual([], report["errors"])

    def test_source_action_hash_tampering_is_detected(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "action-ontology.json"
            profile = self.build_to(path)
            profile["actions"][0]["source_action_sha256"] = "0" * 64
            path.write_text(json.dumps(profile), encoding="utf-8")

            report = VALIDATOR.validate_profile(path)

            self.assertFalse(report["source_integrity_valid"])
            self.assertTrue(
                any("source action hash mismatch" in error for error in report["errors"])
            )

    def test_unresolved_mapping_blocks_a_frozen_profile(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "action-ontology.json"
            profile = self.build_to(path)
            profile["status"] = "frozen"
            path.write_text(json.dumps(profile), encoding="utf-8")

            report = VALIDATOR.validate_profile(path)

            self.assertFalse(report["formal_ready"])
            self.assertTrue(
                any("unresolved operational mappings" in error for error in report["errors"])
            )


if __name__ == "__main__":
    unittest.main()
