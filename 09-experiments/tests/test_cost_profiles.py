import csv
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace


EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = EXPERIMENT_ROOT / "scripts"
SCHEMA_PATH = EXPERIMENT_ROOT / "data_schema" / "cost_profile.schema.json"
EXAMPLES_DIR = EXPERIMENT_ROOT / "examples"
REAL_CASES_DIR = EXPERIMENT_ROOT / "real_cases"


def load_script(name):
    path = SCRIPTS_DIR / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"test_{name}", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


run_mvp = load_script("run_mvp")
builder = load_script("build_cost_profile_drafts")
validator = load_script("validate_cost_profile")


class CostRegimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.case_dir = EXAMPLES_DIR / "C01"
        cls.config = run_mvp.load_json(cls.case_dir / "case_config.json")
        cls.actions = run_mvp.load_json(cls.case_dir / "acquisition_actions.json")

    def rubric_bundle(self, status="frozen", drop_last=False):
        entries = [
            {
                "case_id": self.config["case_id"],
                "action_id": action["action_id"],
                "components": {"E": 1, "V": 1, "D": 1, "A": 0, "R": 0},
            }
            for action in self.actions
        ]
        if drop_last:
            entries.pop()
        return {
            "document": {
                "profile_id": "test-rubric-v1",
                "version": "1.0.0",
                "status": status,
                "regime": "rubric",
                "scope": {"case_ids": [self.config["case_id"]]},
                "scoring": {
                    "weights": {"E": 1, "V": 1, "D": 1, "A": 1, "R": 1},
                    "scale": 2,
                    "rounding": "half_up",
                    "minimum_cost": 1,
                    "maximum_cost": 4,
                },
                "actions": entries,
            },
            "sha256": "a" * 64,
            "source_path": "test-rubric.json",
        }

    def measured_bundle(self):
        return {
            "document": {
                "profile_id": "test-measured-v1",
                "version": "1.0.0",
                "status": "frozen",
                "regime": "measured",
                "scope": {"case_ids": [self.config["case_id"]]},
                "scoring": {"method": "precomputed_continuous"},
                "actions": [
                    {
                        "case_id": self.config["case_id"],
                        "action_id": action["action_id"],
                        "measured_cost": 1.25 + index / 10,
                    }
                    for index, action in enumerate(self.actions)
                ],
            },
            "sha256": "b" * 64,
            "source_path": "test-measured.json",
        }

    def test_legacy_is_a_non_mutating_exact_copy_without_metadata(self):
        original = json.loads(json.dumps(self.actions))

        resolved, metadata = run_mvp.apply_cost_regime(
            self.actions,
            self.config["case_id"],
        )

        self.assertEqual(original, resolved)
        self.assertEqual(original, self.actions)
        self.assertIsNot(resolved, self.actions)
        self.assertIsNone(metadata)

    def test_uniform_is_reproducible_and_does_not_modify_source_actions(self):
        original = json.loads(json.dumps(self.actions))

        first, first_metadata = run_mvp.apply_cost_regime(
            self.actions,
            self.config["case_id"],
            "uniform",
        )
        second, second_metadata = run_mvp.apply_cost_regime(
            self.actions,
            self.config["case_id"],
            "uniform",
        )

        self.assertTrue(all(action["cost"] == 1.0 for action in first))
        self.assertEqual(first, second)
        self.assertEqual(first_metadata, second_metadata)
        self.assertEqual(64, len(first_metadata["cost_profile_sha256"]))
        self.assertEqual(original, self.actions)

    def test_rubric_uses_half_up_composition_and_records_identity(self):
        resolved, metadata = run_mvp.apply_cost_regime(
            self.actions,
            self.config["case_id"],
            "rubric",
            self.rubric_bundle(),
        )

        self.assertTrue(all(action["cost"] == 2.0 for action in resolved))
        self.assertEqual("rubric", metadata["cost_regime"])
        self.assertEqual("test-rubric-v1", metadata["cost_profile_id"])
        self.assertEqual("a" * 64, metadata["cost_profile_sha256"])

    def test_measured_preserves_continuous_values_reproducibly(self):
        bundle = self.measured_bundle()

        first, first_metadata = run_mvp.apply_cost_regime(
            self.actions,
            self.config["case_id"],
            "measured",
            bundle,
        )
        second, second_metadata = run_mvp.apply_cost_regime(
            self.actions,
            self.config["case_id"],
            "measured",
            bundle,
        )

        self.assertEqual(first, second)
        self.assertEqual(first_metadata, second_metadata)
        self.assertEqual(1.25, first[0]["cost"])
        self.assertEqual(1.95, first[-1]["cost"])

    def test_draft_profile_is_rejected_from_formal_execution(self):
        with self.assertRaisesRegex(ValueError, "status='frozen'"):
            run_mvp.apply_cost_regime(
                self.actions,
                self.config["case_id"],
                "rubric",
                self.rubric_bundle(status="draft"),
            )

    def test_incomplete_profile_is_rejected_from_formal_execution(self):
        with self.assertRaisesRegex(ValueError, "coverage mismatch"):
            run_mvp.apply_cost_regime(
                self.actions,
                self.config["case_id"],
                "rubric",
                self.rubric_bundle(drop_last=True),
            )

    def test_profile_run_records_version_and_hash_without_editing_case_file(self):
        action_path = self.case_dir / "acquisition_actions.json"
        before = action_path.read_bytes()

        rows, traces = run_mvp.execute_case(
            self.case_dir,
            cost_regime="uniform",
        )

        self.assertEqual(before, action_path.read_bytes())
        self.assertEqual("uniform", rows[0]["cost_regime"])
        self.assertEqual("1.0.0", rows[0]["cost_profile_version"])
        self.assertEqual(
            rows[0]["cost_profile_sha256"],
            traces[0]["result"]["cost_profile_sha256"],
        )

    def test_manifest_identity_distinguishes_legacy_and_uniform_provenance(self):
        legacy, legacy_metadata = run_mvp.apply_cost_regime(
            self.actions, self.config["case_id"], "legacy"
        )
        uniform, uniform_metadata = run_mvp.apply_cost_regime(
            self.actions, self.config["case_id"], "uniform"
        )
        legacy_identity = run_mvp.cost_profile_identity(
            legacy, self.config["case_id"], "legacy", legacy_metadata
        )
        uniform_identity = run_mvp.cost_profile_identity(
            uniform, self.config["case_id"], "uniform", uniform_metadata
        )
        self.assertEqual(
            "case_embedded_legacy_exogenous_cost", legacy_identity["provenance"]
        )
        self.assertEqual(
            "uniform_frozen_exogenous_cost", uniform_identity["provenance"]
        )
        self.assertNotEqual(legacy_identity["sha256"], uniform_identity["sha256"])


class DraftBuilderAndValidatorTests(unittest.TestCase):
    def build_drafts(self, output_dir):
        return builder.build(
            SimpleNamespace(
                examples_dir=EXAMPLES_DIR,
                real_cases_dir=REAL_CASES_DIR,
                output_dir=output_dir,
                created_utc="2026-07-14T08:00:00Z",
                profile_version="0.1.0-draft",
                seed=20260714,
            )
        )

    def test_builder_covers_all_cases_and_blinds_rating_packets(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "drafts"
            manifest = self.build_drafts(output_dir)

            with (output_dir / "cost-rating-packet-A.csv").open(
                "r", encoding="utf-8", newline=""
            ) as handle:
                packet_a = list(csv.DictReader(handle))
            with (output_dir / "cost-rating-packet-B.csv").open(
                "r", encoding="utf-8", newline=""
            ) as handle:
                packet_b = list(csv.DictReader(handle))

            self.assertEqual(12, manifest["case_count"])
            self.assertEqual(72, manifest["action_count"])
            self.assertEqual(72, len(packet_a))
            self.assertEqual(72, len(packet_b))
            self.assertEqual(
                {row["item_id"] for row in packet_a},
                {row["item_id"] for row in packet_b},
            )
            self.assertNotEqual(
                [row["item_id"] for row in packet_a],
                [row["item_id"] for row in packet_b],
            )
            self.assertNotIn("legacy_cost", packet_a[0])
            self.assertNotIn("recoverable_claim_ids", packet_a[0])
            self.assertNotIn("expected_effects", packet_a[0])

    def test_generated_drafts_are_valid_but_not_formally_ready(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "drafts"
            self.build_drafts(output_dir)

            rubric = validator.readiness_report(
                output_dir / "rubric-cost-profile-v0.1-draft.json"
            )
            measured = validator.readiness_report(
                output_dir / "measured-cost-profile-v0.1-draft.json"
            )

            self.assertTrue(rubric["schema_valid"])
            self.assertTrue(rubric["coverage_valid"])
            self.assertFalse(rubric["formal_ready"])
            self.assertEqual(360, rubric["pending_component_values"])
            self.assertEqual(0, rubric["pending_measured_costs"])
            self.assertTrue(measured["schema_valid"])
            self.assertTrue(measured["coverage_valid"])
            self.assertFalse(measured["formal_ready"])
            self.assertEqual(0, measured["pending_component_values"])
            self.assertEqual(72, measured["pending_measured_costs"])

    def test_require_frozen_flags_a_draft_without_mutating_it(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "drafts"
            self.build_drafts(output_dir)
            profile_path = output_dir / "rubric-cost-profile-v0.1-draft.json"
            before = profile_path.read_bytes()

            report = validator.readiness_report(
                profile_path,
                require_frozen=True,
            )

            self.assertIn("profile status is not frozen", report["errors"])
            self.assertFalse(report["formal_ready"])
            self.assertEqual(before, profile_path.read_bytes())

    def test_builder_refuses_to_overwrite_existing_output(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "drafts"
            self.build_drafts(output_dir)

            with self.assertRaisesRegex(FileExistsError, "Refusing to overwrite"):
                self.build_drafts(output_dir)

    def test_frozen_rubric_schema_rejects_unfilled_components(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "drafts"
            self.build_drafts(output_dir)
            profile = json.loads(
                (output_dir / "rubric-cost-profile-v0.1-draft.json").read_text(
                    encoding="utf-8"
                )
            )
            profile["status"] = "frozen"
            profile["scoring"].update(
                {
                    "weights": {"E": 1, "V": 1, "D": 1, "A": 1, "R": 1},
                    "scale": 3.75,
                    "rounding": "half_up",
                    "minimum_cost": 1,
                    "maximum_cost": 4,
                }
            )
            schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))

            errors = validator.schema_errors(profile, schema)

            self.assertTrue(errors)
            self.assertTrue(any("components" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
