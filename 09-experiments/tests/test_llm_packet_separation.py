import gzip
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = EXPERIMENT_ROOT / "scripts" / "build_llm_evaluation_packets.py"


def load_builder():
    spec = importlib.util.spec_from_file_location(
        "build_llm_evaluation_packets", SCRIPT_PATH
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


builder = load_builder()


def source_record():
    pointer = {"artifact_id": "artifact-public", "record_id": "event-public-1"}
    payload = {
        "operation": "EVENT_EXECUTE",
        "process": "powershell.exe",
        "command": "Compress-Archive C:\\Temp\\A.txt C:\\Temp\\A.zip",
    }
    return builder.make_packet_record("local_log", pointer, payload)


def canonical_observation():
    return {
        "canonical_claim_id": "C07-EC-001",
        "source_type": "local_log",
        "subject": {"entity_type": "process", "value": "powershell.exe"},
        "predicate": "created",
        "object": {"entity_type": "file", "value": "C:\\Temp\\A.zip"},
        "source_pointer": {
            "artifact_id": "artifact-public",
            "record_id": "event-public-1",
        },
    }


def packet_pair():
    return builder.build_packet_pair(
        case_id="C07-test-case",
        split="test",
        packet_role="positive",
        support_ceiling="G3_campaign",
        records=[source_record()],
        acceptable_observations=[canonical_observation()],
    )


class PacketIdentityTests(unittest.TestCase):
    def test_public_bytes_never_contain_canonical_or_gold_id(self):
        public, private = packet_pair()
        payload = builder.canonical_json(public)

        self.assertNotIn(b"C07-EC-001", payload)
        self.assertNotIn(b"GOLD-", payload)
        self.assertNotIn("canonical_claim_id", public)
        self.assertRegex(private["acceptable_observations"][0]["gold_claim_id"], r"^GOLD-[A-F0-9]{24}$")

    def test_private_gold_mutation_does_not_change_public_bytes_or_request_id(self):
        public, private = packet_pair()
        before = builder.canonical_json(public)
        request_before = public["request_id"]

        private["acceptable_observations"][0]["predicate"] = (
            "changed_only_in_private"
        )

        self.assertEqual(before, builder.canonical_json(public))
        self.assertEqual(request_before, public["request_id"])
        self.assertEqual(request_before, builder.derive_request_id(public))

    def test_candidate_id_binds_condition_attempt_and_output_index(self):
        ids = {
            builder.derive_candidate_claim_id(
                "REQ-" + "A" * 24,
                "general_compiler",
                attempt_index,
                output_index,
            )
            for attempt_index in (0, 1)
            for output_index in (0, 1)
        }

        self.assertEqual(4, len(ids))
        self.assertTrue(all(value.startswith("CC-") for value in ids))

    def test_write_bundle_physically_separates_public_and_private_files(self):
        public, private = packet_pair()
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "bundle"
            manifest = builder.write_bundle(
                output,
                public_rows=[public],
                private_rows=[private],
                public_catalog={"catalog_version": "test-v1", "artifacts": []},
                metadata={"split": "test", "status": "draft"},
            )

            self.assertEqual(
                {
                    "context_packets.jsonl.gz",
                    "public_cti_catalog.json",
                    "input_manifest.json",
                },
                {path.name for path in (output / "public").iterdir()},
            )
            self.assertEqual(
                {"observation_gold.jsonl.gz", "gold_manifest.json"},
                {path.name for path in (output / "private").iterdir()},
            )
            self.assertEqual("separated", manifest["separation_status"])
            with gzip.open(
                output / "public" / "context_packets.jsonl.gz",
                "rt",
                encoding="utf-8",
            ) as handle:
                self.assertEqual(public, json.loads(handle.readline()))


class PacketSourceAdapterTests(unittest.TestCase):
    def test_development_and_test_counts_are_frozen(self):
        with tempfile.TemporaryDirectory() as temp:
            dev = builder.build_split(
                REPOSITORY_ROOT,
                "development",
                Path(temp) / "development",
            )
            test = builder.build_split(
                REPOSITORY_ROOT,
                "test",
                Path(temp) / "test",
            )

            self.assertEqual({"positive": 26, "null": 26}, dev["packet_counts"])
            self.assertEqual({"positive": 32, "null": 32}, test["packet_counts"])
            self.assertEqual(6, test["case_count"])

    def test_positive_packet_has_no_target_marker_and_private_allows_multiple_gold(self):
        public, private = builder.build_case_fixture_with_two_distractors()

        self.assertNotIn("target", json.dumps(public).casefold())
        self.assertGreaterEqual(len(public["records"]), 3)
        self.assertGreaterEqual(len(private["acceptable_observations"]), 1)

    def test_repeated_build_is_byte_identical(self):
        with tempfile.TemporaryDirectory() as temp:
            first = Path(temp) / "first"
            second = Path(temp) / "second"
            builder.build_split(REPOSITORY_ROOT, "test", first)
            builder.build_split(REPOSITORY_ROOT, "test", second)

            self.assertEqual(
                (first / "public" / "input_manifest.json").read_bytes(),
                (second / "public" / "input_manifest.json").read_bytes(),
            )
            self.assertEqual(
                (first / "public" / "context_packets.jsonl.gz").read_bytes(),
                (second / "public" / "context_packets.jsonl.gz").read_bytes(),
            )

    def test_witfoo_aggregate_constituents_are_flagged_for_human_audit(self):
        case_dir = (
            REPOSITORY_ROOT
            / "09-experiments"
            / "real_cases"
            / "C12-witfoo-precinct6-f10c7270"
        )
        claims = json.loads(
            (case_dir / "evidence_claims.json").read_text(encoding="utf-8")
        )
        records, _ = builder.load_case_records(REPOSITORY_ROOT, case_dir)
        claimed_record_ids = {
            claim["source_pointer"]["record_id"] for claim in claims
        }
        null_pool = [
            record
            for record in records
            if record["source_pointer"]["record_id"] not in claimed_record_ids
        ]
        aggregate_contributors = [
            record
            for record in null_pool
            if (
                record["source_payload"].get("lead", {}).get("product", {}).get("name")
                == "ASA Firewall"
            )
        ]

        self.assertGreater(len(aggregate_contributors), 0)
        for record in aggregate_contributors:
            self.assertIn(
                "constituent_of_aggregate_observation",
                builder.null_review_flags(record),
            )


if __name__ == "__main__":
    unittest.main()
