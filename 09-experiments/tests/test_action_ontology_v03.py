import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
EXP = ROOT / "09-experiments"
SCRIPTS = EXP / "scripts"
COHORT = EXP / "governance" / "cohorts" / "real-case-cohort-v0.3.json"


def load_script(name):
    path = SCRIPTS / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"test_{name}", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


BUILDER = load_script("build_action_ontology_v03")
VALIDATOR = load_script("validate_action_ontology_v03")


class ActionOntologyV03Tests(unittest.TestCase):
    def build_to(self, path):
        profile = BUILDER.build_profile(COHORT, "2026-07-18T00:00:00Z")
        path.write_text(
            json.dumps(profile, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        return profile

    def test_real_only_profile_has_expected_case_action_and_phase_counts(self):
        profile = BUILDER.build_profile(COHORT, "2026-07-18T00:00:00Z")

        self.assertEqual([f"C{number:02d}" for number in range(1, 10)], profile["scope"]["case_ids"])
        self.assertEqual(50, profile["scope"]["action_count"])
        self.assertEqual(19, sum(row["phase"] == "calibration" for row in profile["actions"]))
        self.assertEqual(31, sum(row["phase"] == "development" for row in profile["actions"]))
        self.assertEqual(7, len({row["action_type"] for row in profile["actions"]}))
        self.assertNotIn("malware_analysis", {row["action_type"] for row in profile["actions"]})
        self.assertEqual("unassigned_and_sealed", profile["data_boundary"]["canonical_C10_plus"])

    def test_canonical_and_source_ids_replay_every_real_action(self):
        profile = BUILDER.build_profile(COHORT, "2026-07-18T00:00:00Z")

        for row in profile["actions"]:
            source_path = ROOT / row["source_action_ref"]
            source_actions = json.loads(source_path.read_text(encoding="utf-8"))
            source = next(
                action
                for action in source_actions
                if action["action_id"] == row["source_action_id"]
            )
            self.assertEqual(
                BUILDER.canonical_action_id(row["case_id"], row["source_action_id"]),
                row["action_id"],
            )
            self.assertEqual(row["target"], source["target"])
            self.assertEqual(VALIDATOR.canonical_sha256(source), row["source_action_sha256"])

    def test_toy_actions_and_legacy_scalar_cost_do_not_leak(self):
        profile = BUILDER.build_profile(COHORT, "2026-07-18T00:00:00Z")

        self.assertTrue(
            all(
                not row["source_case_id"].startswith(("C01-", "C02-", "C03-"))
                for row in profile["actions"]
            )
        )
        self.assertTrue(all("cost" not in row for row in profile["actions"]))
        self.assertTrue(all("cost_breakdown" not in row for row in profile["actions"]))

    def test_generated_draft_is_valid_replayable_and_not_formally_ready(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "action-ontology-v0.3.json"
            self.build_to(path)

            report = VALIDATOR.validate_profile(path)

            self.assertTrue(report["schema_valid"])
            self.assertTrue(report["source_alias_integrity_valid"])
            self.assertEqual(9, report["canonical_case_count"])
            self.assertEqual(50, report["action_count"])
            self.assertEqual(7, report["action_type_count"])
            self.assertEqual(0, report["toy_action_count"])
            self.assertEqual(500, report["unresolved_mapping_count"])
            self.assertFalse(report["formal_ready"])
            self.assertEqual([], report["errors"])

    def test_source_action_hash_tampering_is_detected(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "action-ontology-v0.3.json"
            profile = self.build_to(path)
            profile["actions"][0]["source_action_sha256"] = "0" * 64
            path.write_text(json.dumps(profile), encoding="utf-8")

            report = VALIDATOR.validate_profile(path)

            self.assertFalse(report["source_alias_integrity_valid"])
            self.assertTrue(
                any("source action hash mismatch" in error for error in report["errors"])
            )


if __name__ == "__main__":
    unittest.main()
