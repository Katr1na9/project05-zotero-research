import importlib.util
import gzip
import json
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "build_llm_compiler_pilot.py"
SPEC = importlib.util.spec_from_file_location("build_llm_compiler_pilot", SCRIPT)
pilot = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(pilot)


class PilotSampleTests(unittest.TestCase):
    def test_model_input_is_separated_from_gold_claim(self):
        claim = {
            "claim_id": "C09-EC-001",
            "case_id": "C09-test",
            "source_type": "network_summary",
            "tags": ["critical"],
            "source_pointer": {"artifact_id": "artifact", "record_id": "event-1"},
        }
        source_payload = {
            "event_id": "event-1",
            "object": "FLOW",
            "process": ["powershell.exe"],
        }

        sample = pilot.make_sample(claim, "ecar_event", source_payload)

        self.assertEqual("C09-EC-001", sample["sample_id"])
        self.assertEqual(claim, sample["gold_claim"])
        self.assertNotIn("gold_claim", sample["model_input"])
        self.assertNotIn("tags", sample["model_input"])
        self.assertEqual(source_payload, sample["model_input"]["source_payload"])

    def test_benign_context_claim_is_tagged_as_context_required_control(self):
        claim = {
            "claim_id": "C07-EC-004",
            "case_id": "C07-test",
            "claim_type": "benign_maintenance",
            "source_pointer": {"artifact_id": "artifact", "record_id": "event-2"},
        }

        sample = pilot.make_sample(claim, "provenance_edge", {"event_uuid": "event-2"})

        self.assertEqual("context_required_control", sample["evaluation_role"])

    def test_pilot_jsonl_can_be_written_as_gzip(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "pilot.jsonl.gz"
            pilot.write_jsonl(path, [{"sample_id": "S1"}])

            with gzip.open(path, "rt", encoding="utf-8") as handle:
                self.assertEqual({"sample_id": "S1"}, json.loads(handle.readline()))


if __name__ == "__main__":
    unittest.main()
