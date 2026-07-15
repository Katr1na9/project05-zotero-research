import csv
import importlib.util
import json
import re
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
EXP = ROOT / "09-experiments"
SCRIPT = EXP / "scripts" / "build_annotation_round2_packets.py"
CASES_ROOT = EXP / "real_cases"
FROZEN_PACKET = EXP / "annotation" / "c07_c11_v0.2"
PROTOCOL = (
    EXP
    / "annotation"
    / "protocols"
    / "c07_c11_round2-codebook-v0.1.md"
)
SOURCE_PACKAGE = (
    EXP
    / "annotation"
    / "source_excerpts"
    / "c07_c11_round2_v0.1"
)


def load_module():
    spec = importlib.util.spec_from_file_location(
        "build_annotation_round2_packets", SCRIPT
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def read_jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def tree_hashes(root):
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file()
    }


class AnnotationRound2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load_module()

    def build_temp(self, output):
        return self.module.build(CASES_ROOT, Path(output))

    def test_build_is_deterministic_and_does_not_touch_frozen_v02(self):
        frozen_before = tree_hashes(FROZEN_PACKET)
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            self.build_temp(first)
            self.build_temp(second)
            for relative in (
                "packet_manifest.json",
                "public/claim_items.jsonl",
                "public/intent_items.jsonl",
                "public/granularity_items.jsonl",
                "annotator_A/PACKAGE-METADATA.json",
                "annotator_B/PACKAGE-METADATA.json",
            ):
                self.assertEqual(
                    (Path(first) / relative).read_bytes(),
                    (Path(second) / relative).read_bytes(),
                )
        self.assertEqual(frozen_before, tree_hashes(FROZEN_PACKET))

    def test_pointer_controls_are_balanced_within_artifact_and_hidden(self):
        with tempfile.TemporaryDirectory() as output:
            root = Path(output)
            manifest = self.build_temp(root)
            key = json.loads(
                (root / "admin" / "admin_key.json").read_text(encoding="utf-8")
            )["claim"]
            counts = {"correct": 0, "deliberately_wrong": 0}
            presented = []
            for row in key.values():
                condition = row["source_pointer_condition"]
                counts[condition] += 1
                original = row["original_source_pointer"]
                candidate = row["presented_source_pointer"]
                presented.append(json.dumps(candidate, sort_keys=True))
                self.assertEqual(original["artifact_id"], candidate["artifact_id"])
                if condition == "correct":
                    self.assertEqual(original, candidate)
                else:
                    self.assertNotEqual(original, candidate)
                    self.assertTrue(row["pointer_donor_claim_id"])
            self.assertEqual(counts, {"correct": 13, "deliberately_wrong": 14})
            self.assertEqual(len(presented), len(set(presented)))
            self.assertEqual(
                manifest["pointer_control"]["condition_counts"], counts
            )

            public_blob = (root / "public" / "claim_items.jsonl").read_text(
                encoding="utf-8"
            )
            for forbidden in (
                "source_pointer_condition",
                "original_source_pointer",
                "pointer_donor",
                "case_id",
                "claim_id",
            ):
                self.assertNotIn(forbidden, public_blob)

    def test_a_and_b_have_distinct_metadata_order_and_hashes_but_same_items(self):
        with tempfile.TemporaryDirectory() as output:
            root = Path(output)
            manifest = self.build_temp(root)
            package_a = manifest["packages"]["A"]
            package_b = manifest["packages"]["B"]
            self.assertNotEqual(package_a["package_id"], package_b["package_id"])
            self.assertNotEqual(package_a["issued_utc"], package_b["issued_utc"])
            self.assertNotEqual(package_a["seed"], package_b["seed"])
            for filename in self.module.TASK_FILES.values():
                rows_a = read_jsonl(root / "annotator_A" / "public" / filename)
                rows_b = read_jsonl(root / "annotator_B" / "public" / filename)
                ids_a = [row["blind_id"] for row in rows_a]
                ids_b = [row["blind_id"] for row in rows_b]
                self.assertEqual(set(ids_a), set(ids_b))
                self.assertNotEqual(ids_a, ids_b)
                self.assertNotEqual(
                    package_a["public_file_sha256"][filename],
                    package_b["public_file_sha256"][filename],
                )
                self.assertTrue(
                    all(row["package_id"] == package_a["package_id"] for row in rows_a)
                )
                self.assertTrue(
                    all(row["package_id"] == package_b["package_id"] for row in rows_b)
                )

    def test_public_views_are_sanitized_and_templates_are_blank(self):
        leak_patterns = [
            re.compile(r"\bGT\b"),
            re.compile(r"TA5\.1", re.IGNORECASE),
            re.compile(r"ground[ _-]?truth", re.IGNORECASE),
            re.compile(r"C\d\d-EC-\d+"),
            re.compile(r"recoverable_claim_ids", re.IGNORECASE),
            re.compile(r"computed_granularity", re.IGNORECASE),
        ]
        with tempfile.TemporaryDirectory() as output:
            root = Path(output)
            manifest = self.build_temp(root)
            self.assertFalse(manifest["human_labels_present"])
            for annotator in ("annotator_A", "annotator_B"):
                for filename in self.module.TASK_FILES.values():
                    blob = (root / annotator / "public" / filename).read_text(
                        encoding="utf-8"
                    )
                    for pattern in leak_patterns:
                        self.assertIsNone(pattern.search(blob), pattern.pattern)

                claims = read_jsonl(
                    root / annotator / "public" / "claim_items.jsonl"
                )
                granularities = read_jsonl(
                    root / annotator / "public" / "granularity_items.jsonl"
                )
                self.assertTrue(all(row["notes"] == "" for row in claims))
                for state in granularities:
                    for claim in state["visible_claims"]:
                        self.assertEqual(claim["notes"], "")
                        self.assertEqual(claim["mapped_tactic"], [])
                        self.assertEqual(claim["mapped_technique"], [])

                for template_name, _ in self.module.TEMPLATE_SPECS.values():
                    with (root / annotator / template_name).open(
                        encoding="utf-8-sig", newline=""
                    ) as handle:
                        rows = list(csv.DictReader(handle))
                    for row in rows:
                        self.assertTrue(row["blind_id"])
                        self.assertTrue(
                            all(not value for key, value in row.items() if key != "blind_id")
                        )

    def test_protocol_locks_direct_target_not_downstream_rule(self):
        text = PROTOCOL.read_text(encoding="utf-8")
        self.assertIn("只标动作请求**直接指向**的 CTI 节点", text)
        self.assertIn("不沿 CTI 边传播标签", text)
        self.assertIn("下游", text)
        self.assertIn("human_labels_present=false", text)

    def test_committed_source_manifest_resolves_presented_pointers_only(self):
        manifest = json.loads(
            (SOURCE_PACKAGE / "source_excerpt_manifest.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(
            manifest["package_version"],
            "c07_c11_round2_source_excerpts_v0.1",
        )
        self.assertEqual(
            manifest["annotation_packet_version"], "c07_c11_round2_v0.1"
        )
        self.assertEqual(manifest["excerpt_count"], 27)
        self.assertFalse(manifest["human_labels_present"])
        self.assertIn("presented", manifest["pointer_semantics"].casefold())
        self.assertEqual(
            manifest["claim_items_sha256"],
            self.module.sha256_file(
                EXP
                / "annotation"
                / "c07_c11_round2_v0.1"
                / "public"
                / "claim_items.jsonl"
            ),
        )

        local_path = SOURCE_PACKAGE / "local" / "claim_source_excerpts.jsonl"
        if local_path.is_file():
            self.assertEqual(
                manifest["local_excerpt_file"]["sha256"],
                self.module.sha256_file(local_path),
            )
            public = {
                row["blind_id"]: row["source_pointer"]
                for row in read_jsonl(
                    EXP
                    / "annotation"
                    / "c07_c11_round2_v0.1"
                    / "public"
                    / "claim_items.jsonl"
                )
            }
            excerpts = read_jsonl(local_path)
            self.assertEqual(set(public), {row["blind_id"] for row in excerpts})
            for row in excerpts:
                self.assertEqual(row["source_pointer"], public[row["blind_id"]])
                self.assertNotIn("source_pointer_condition", row)
                self.assertNotIn("original_source_pointer", row)

    def test_nonempty_output_is_rejected(self):
        with tempfile.TemporaryDirectory() as output:
            root = Path(output)
            (root / "sentinel.txt").write_text("keep", encoding="utf-8")
            with self.assertRaisesRegex(FileExistsError, "refusing overwrite"):
                self.build_temp(root)
            self.assertEqual(
                (root / "sentinel.txt").read_text(encoding="utf-8"), "keep"
            )


if __name__ == "__main__":
    unittest.main()
