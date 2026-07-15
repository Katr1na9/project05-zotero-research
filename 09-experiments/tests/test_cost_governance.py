import copy
import csv
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker


ROOT = Path(__file__).resolve().parents[2]
EXP = ROOT / "09-experiments"


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


MVP = load_module(EXP / "scripts" / "run_mvp.py", "cost_governance_mvp")
BUILDER = load_module(
    EXP / "scripts" / "build_cost_governance.py", "cost_governance_builder"
)


class CostGovernanceTests(unittest.TestCase):
    def test_generated_drafts_validate_and_remain_non_runnable(self):
        schema = json.loads(
            (EXP / "data_schema" / "cost_profile.schema.json").read_text(
                encoding="utf-8"
            )
        )
        validator = Draft202012Validator(schema, format_checker=FormatChecker())
        for name in (
            "cost-rubric-v0.1-draft.json",
            "cost-measured-v0.1-draft.json",
        ):
            profile = json.loads(
                (EXP / "governance" / "profiles" / name).read_text(encoding="utf-8")
            )
            self.assertEqual([], list(validator.iter_errors(profile)))
            self.assertEqual("draft", profile["status"])
            self.assertEqual(72, len(profile["actions"]))

    def test_rating_packets_are_independent_and_hide_legacy_outcomes(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest = BUILDER.build(root / "profiles", root / "annotation")
            self.assertFalse(manifest["formal_run_allowed"])
            packets = []
            for code in ("A", "B"):
                path = root / "annotation" / "public" / f"cost_ratings_{code}.csv"
                with path.open(encoding="utf-8", newline="") as handle:
                    rows = list(csv.DictReader(handle))
                self.assertEqual(72, len(rows))
                self.assertNotIn("legacy_cost", rows[0])
                self.assertFalse(any("recoverable" in field for field in rows[0]))
                self.assertTrue(all(not row[c] for row in rows for c in "EVDAR"))
                packets.append([row["item_id"] for row in rows])
            self.assertNotEqual(packets[0], packets[1])

    def test_legacy_and_uniform_are_non_destructive(self):
        case = EXP / "examples" / "C01"
        actions = MVP.load_json(case / "acquisition_actions.json")
        original = copy.deepcopy(actions)
        legacy, metadata = MVP.apply_cost_regime(
            actions, "C01-linux-provenance", "legacy"
        )
        self.assertEqual(original, legacy)
        self.assertIsNone(metadata)
        uniform, metadata = MVP.apply_cost_regime(
            actions, "C01-linux-provenance", "uniform"
        )
        self.assertEqual(original, actions)
        self.assertTrue(all(action["cost"] == 1.0 for action in uniform))
        self.assertEqual("uniform", metadata["cost_regime"])
        self.assertEqual(64, len(metadata["cost_profile_sha256"]))

    def test_draft_and_incomplete_profiles_are_rejected(self):
        case = EXP / "examples" / "C01"
        actions = MVP.load_json(case / "acquisition_actions.json")
        path = EXP / "governance" / "profiles" / "cost-rubric-v0.1-draft.json"
        bundle = MVP.load_cost_profile(path)
        with self.assertRaisesRegex(ValueError, "status='frozen'"):
            MVP.apply_cost_regime(
                actions, "C01-linux-provenance", "rubric", bundle
            )

        frozen = copy.deepcopy(bundle)
        frozen["document"]["status"] = "frozen"
        frozen["document"]["actions"] = [
            entry
            for entry in frozen["document"]["actions"]
            if entry["action_id"] != "C01-AA-008"
        ]
        for entry in frozen["document"]["actions"]:
            entry["components"] = dict.fromkeys("EVDAR", 0)
        with self.assertRaisesRegex(ValueError, "coverage mismatch"):
            MVP.apply_cost_regime(
                actions, "C01-linux-provenance", "rubric", frozen
            )


if __name__ == "__main__":
    unittest.main()
