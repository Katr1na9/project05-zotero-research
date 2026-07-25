import importlib
import json
import unittest
from pathlib import Path

import yaml


try:
    selection_api = importlib.import_module("src.actions.selection")
except (ImportError, ModuleNotFoundError):
    selection_api = None


ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "tests" / "fixtures" / "TWIN-COUNTEREXAMPLE-001"


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_yaml(path):
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))


class TwinDistinguishingActionSelectionP4IntegrationTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(
            selection_api, "P4 distinguishing-action selector API is missing"
        )

    def test_twin_catalog_recomputes_frozen_allowed_and_forbidden_actions(self):
        artifact = load_json(FIXTURE / "expected" / "counterexample.json")
        expected = load_yaml(FIXTURE / "expected" / "outcome.yaml")
        catalog = load_yaml(ROOT / "configs" / "action-catalog-kernel-v0.8.yaml")

        result = selection_api.DistinguishingActionSelector().select(
            artifact, catalog
        )

        self.assertEqual(tuple(expected["allowed_actions"]), result.allowed_actions)
        self.assertEqual(
            tuple(expected["forbidden_actions"]), result.forbidden_actions
        )
        self.assertEqual(
            {
                "allowed_actions": expected["allowed_actions"],
                "forbidden_actions": expected["forbidden_actions"],
            },
            result.to_outcome_fields(),
        )
        self.assertNotIn("system_status", result.to_outcome_fields())
        self.assertNotIn("CERTIFIED_STOP", json.dumps(result.to_outcome_fields()))


if __name__ == "__main__":
    unittest.main()
