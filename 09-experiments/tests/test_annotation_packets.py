import csv
import importlib.util
import json
import re
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "09-experiments" / "scripts" / "build_annotation_packets.py"
CASES_ROOT = ROOT / "09-experiments" / "real_cases"
FROZEN_PACKET = (
    ROOT / "09-experiments" / "annotation" / "c07_c11_v0.2"
)


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
            self.module.build_packets(CASES_ROOT, Path(first), seed=20260712)
            self.module.build_packets(CASES_ROOT, Path(second), seed=20260712)
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
            summary = self.module.build_packets(CASES_ROOT, root, seed=20260712)
            claims = read_jsonl(root / "public" / "claim_items.jsonl")
            intents = read_jsonl(root / "public" / "intent_items.jsonl")
            states = read_jsonl(root / "public" / "granularity_items.jsonl")
            self.assertEqual(len(claims), 27)
            self.assertEqual(len(intents), 27)
            self.assertEqual(len(states), 60)
            self.assertEqual(summary["independent_case_count"], 5)
            self.assertEqual(summary["annotation_item_total"], 114)
            self.assertEqual(
                summary["case_prefixes"],
                ["C07", "C08", "C09", "C10", "C11"],
            )

    def test_templates_are_blank_and_blind_ids_match_public_items(self):
        with tempfile.TemporaryDirectory() as output:
            root = Path(output)
            self.module.build_packets(CASES_ROOT, root, seed=20260712)
            task_specs = {
                "claim": ("claim_items.jsonl", "claim_annotations.csv"),
                "intent": ("intent_items.jsonl", "intent_annotations.csv"),
                "granularity": ("granularity_items.jsonl", "granularity_annotations.csv"),
            }
            for annotator in ("annotator_A", "annotator_B", "adjudicator"):
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
            self.module.build_packets(CASES_ROOT, root, seed=20260712)
            self.assertFalse((root / "public" / "admin_key.json").exists())
            key = json.loads((root / "admin" / "admin_key.json").read_text(encoding="utf-8"))
            self.assertEqual(set(key), {"claim", "intent", "granularity"})
            self.assertEqual(len(key["claim"]), 27)
            self.assertEqual(len(key["intent"]), 27)

    def test_legacy_scope_can_still_be_rebuilt_explicitly(self):
        with tempfile.TemporaryDirectory() as output:
            summary = self.module.build_packets(
                CASES_ROOT,
                Path(output),
                seed=20260711,
                case_prefixes=("C07", "C08", "C09", "C10"),
                packet_version="c07_c10_v0.1",
            )
            self.assertEqual(summary["claim_item_count"], 19)
            self.assertEqual(summary["intent_item_count"], 22)
            self.assertEqual(summary["granularity_item_count"], 48)
            self.assertEqual(summary["independent_case_count"], 4)

    def test_manifest_hashes_anchor_public_and_source_files(self):
        with tempfile.TemporaryDirectory() as output:
            root = Path(output)
            summary = self.module.build_packets(CASES_ROOT, root)
            for filename, digest in summary["public_file_sha256"].items():
                self.assertEqual(
                    digest,
                    self.module.sha256(root / "public" / filename),
                )
            for case_name, files in summary["source_case_file_sha256"].items():
                for filename, digest in files.items():
                    self.assertEqual(
                        digest,
                        self.module.sha256(CASES_ROOT / case_name / filename),
                    )

    def test_sanitized_public_views_drop_ground_truth_tells(self):
        # Future-round opt-in path: notes and granularity code labels are
        # redacted so annotators cannot read the ground-truth answer.
        leak_patterns = [
            re.compile(r"\bGT\b"),
            re.compile(r"TA5\.1", re.IGNORECASE),
            re.compile(r"ground[ _-]?truth", re.IGNORECASE),
            re.compile(r"C\d\d-EC-\d+"),
            re.compile(r"matched_event_count", re.IGNORECASE),
            re.compile(r"representative_event_uuids", re.IGNORECASE),
        ]
        with tempfile.TemporaryDirectory() as output:
            root = Path(output)
            summary = self.module.build_packets(CASES_ROOT, root, sanitize=True)
            self.assertTrue(summary["public_views_sanitized"])

            claims = read_jsonl(root / "public" / "claim_items.jsonl")
            states = read_jsonl(root / "public" / "granularity_items.jsonl")
            self.assertEqual(len(claims), 27)
            self.assertEqual(len(states), 60)

            for item in claims:
                self.assertEqual(item["notes"], "")
            for item in states:
                for view in item["visible_claims"]:
                    self.assertEqual(view["notes"], "")
                    self.assertEqual(view["mapped_tactic"], [])
                    self.assertEqual(view["mapped_technique"], [])

            for filename in ("claim_items.jsonl", "granularity_items.jsonl"):
                blob = (root / "public" / filename).read_text(encoding="utf-8")
                for pattern in leak_patterns:
                    self.assertIsNone(
                        pattern.search(blob),
                        f"{pattern.pattern} leaked into sanitized {filename}",
                    )

    def test_default_build_is_not_sanitized(self):
        with tempfile.TemporaryDirectory() as output:
            summary = self.module.build_packets(CASES_ROOT, Path(output))
            self.assertNotIn("public_views_sanitized", summary)

    def test_committed_packet_matches_the_frozen_generator(self):
        if not FROZEN_PACKET.is_dir():
            self.skipTest("frozen C07-C11 packet has not been generated")
        with tempfile.TemporaryDirectory() as output:
            root = Path(output)
            self.module.build_packets(CASES_ROOT, root)
            for relative in (
                Path("packet_manifest.json"),
                Path("public/claim_items.jsonl"),
                Path("public/intent_items.jsonl"),
                Path("public/granularity_items.jsonl"),
            ):
                self.assertEqual(
                    (FROZEN_PACKET / relative).read_bytes(),
                    (root / relative).read_bytes(),
                )


if __name__ == "__main__":
    unittest.main()
