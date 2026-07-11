import csv
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "09-experiments" / "scripts" / "build_annotation_packets.py"
CASES_ROOT = ROOT / "09-experiments" / "real_cases"


def load_module():
    spec = importlib.util.spec_from_file_location("build_annotation_packets", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def read_jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


class AnnotationPacketTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(SCRIPT.exists(), "annotation packet generator is missing")
        self.module = load_module()

    def test_public_packets_are_deterministic_and_contain_no_hidden_fields(self):
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            self.module.build_packets(CASES_ROOT, Path(first), seed=20260711)
            self.module.build_packets(CASES_ROOT, Path(second), seed=20260711)
            for filename in ("claim_items.jsonl", "intent_items.jsonl", "granularity_items.jsonl"):
                left = (Path(first) / "public" / filename).read_text(encoding="utf-8")
                right = (Path(second) / "public" / filename).read_text(encoding="utf-8")
                self.assertEqual(left, right)
                for forbidden in (
                    "recoverable_claim_ids",
                    "hidden_claim",
                    "supportable_granularity",
                    "computed_granularity",
                    "planner",
                    "oracle",
                    "case_id",
                    "claim_id",
                    "action_id",
                ):
                    self.assertNotIn(forbidden, left.casefold())

    def test_packet_counts_cover_all_claims_actions_and_bounded_states(self):
        with tempfile.TemporaryDirectory() as output:
            root = Path(output)
            summary = self.module.build_packets(CASES_ROOT, root, seed=20260711)
            claims = read_jsonl(root / "public" / "claim_items.jsonl")
            intents = read_jsonl(root / "public" / "intent_items.jsonl")
            states = read_jsonl(root / "public" / "granularity_items.jsonl")
            self.assertEqual(len(claims), 19)
            self.assertEqual(len(intents), 22)
            self.assertGreater(len(states), 0)
            self.assertLessEqual(len(states), 48)
            self.assertEqual(summary["independent_case_count"], 4)

    def test_templates_are_blank_and_blind_ids_match_public_items(self):
        with tempfile.TemporaryDirectory() as output:
            root = Path(output)
            self.module.build_packets(CASES_ROOT, root, seed=20260711)
            task_specs = {
                "claim": ("claim_items.jsonl", "claim_annotations.csv"),
                "intent": ("intent_items.jsonl", "intent_annotations.csv"),
                "granularity": ("granularity_items.jsonl", "granularity_annotations.csv"),
            }
            for annotator in ("annotator_A", "annotator_B"):
                for _, (items_name, template_name) in task_specs.items():
                    item_ids = {
                        row["blind_id"]
                        for row in read_jsonl(root / "public" / items_name)
                    }
                    with (root / annotator / template_name).open(
                        encoding="utf-8-sig", newline=""
                    ) as handle:
                        rows = list(csv.DictReader(handle))
                    self.assertEqual({row["blind_id"] for row in rows}, item_ids)
                    for row in rows:
                        for field, value in row.items():
                            if field != "blind_id":
                                self.assertEqual(value, "")

    def test_admin_key_is_separate_and_complete(self):
        with tempfile.TemporaryDirectory() as output:
            root = Path(output)
            self.module.build_packets(CASES_ROOT, root, seed=20260711)
            self.assertFalse((root / "public" / "admin_key.json").exists())
            key = json.loads((root / "admin" / "admin_key.json").read_text(encoding="utf-8"))
            self.assertEqual(set(key), {"claim", "intent", "granularity"})
            self.assertEqual(len(key["claim"]), 19)
            self.assertEqual(len(key["intent"]), 22)


if __name__ == "__main__":
    unittest.main()
