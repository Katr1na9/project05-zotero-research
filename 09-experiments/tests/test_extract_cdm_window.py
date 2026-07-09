import importlib.util
import io
import json
import tarfile
import tempfile
import unittest
from pathlib import Path


EXPERIMENT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = EXPERIMENT_DIR / "scripts" / "extract_cdm_window.py"


def load_extractor():
    if not MODULE_PATH.exists():
        return None
    spec = importlib.util.spec_from_file_location(
        "extract_cdm_window",
        MODULE_PATH,
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


extractor = load_extractor()
CDM = "com.bbn.tc.schema.avro.cdm18"


class CdmWindowExtractionTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(
            extractor,
            "extract_cdm_window.py has not been implemented",
        )

    def test_extracts_window_events_and_their_referenced_nodes(self):
        records = [
            self.wrap("Subject", {"uuid": "subject-1", "cmdLine": "nginx"}),
            self.wrap(
                "FileObject",
                {
                    "uuid": "file-1",
                    "baseObject": {"properties": {"map": {"path": "/tmp/x"}}},
                },
            ),
            self.wrap(
                "Event",
                self.event("outside", 99, "subject-1", "file-1"),
            ),
            self.wrap(
                "Event",
                self.event("inside", 150, "subject-1", "file-1"),
            ),
            self.wrap("Subject", {"uuid": "unrelated", "cmdLine": "cron"}),
        ]

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            archive = root / "fixture.tar.gz"
            output_dir = root / "output"
            self.write_archive(archive, records)

            report = extractor.extract_archive_window(
                archive=archive,
                output_dir=output_dir,
                case_id="R-test",
                start_ns=100,
                end_ns=200,
            )

            events = self.read_jsonl(output_dir / "events.jsonl")
            nodes = self.read_jsonl(output_dir / "nodes.jsonl")

        self.assertEqual(["inside"], [event["event_uuid"] for event in events])
        self.assertEqual(
            {"subject-1", "file-1"},
            {node["node_uuid"] for node in nodes},
        )
        self.assertEqual(1, report["events_extracted"])
        self.assertEqual(2, report["referenced_nodes"])
        self.assertEqual(2, report["nodes_resolved"])
        self.assertEqual([], report["unresolved_node_uuids"])

    def test_accepts_export_lines_with_a_trailing_comma(self):
        line = (
            json.dumps(
                self.wrap(
                    "Subject",
                    {"uuid": "subject-1", "cmdLine": "firefox.exe"},
                )
            ).encode("utf-8")
            + b",\n"
        )

        record_type, record = extractor.parse_record(line)

        self.assertEqual("Subject", record_type)
        self.assertEqual("subject-1", record["uuid"])

    @staticmethod
    def wrap(record_type, record):
        return {"datum": {f"{CDM}.{record_type}": record}}

    @staticmethod
    def event(uuid, timestamp, subject, predicate):
        return {
            "uuid": uuid,
            "type": "EVENT_READ",
            "timestampNanos": timestamp,
            "subject": {f"{CDM}.UUID": subject},
            "predicateObject": {f"{CDM}.UUID": predicate},
            "predicateObject2": None,
        }

    @staticmethod
    def write_archive(path, records):
        payload = b"".join(
            json.dumps(record).encode("utf-8") + b"\n"
            for record in records
        )
        info = tarfile.TarInfo("fixture.json")
        info.size = len(payload)
        with tarfile.open(path, "w:gz") as archive:
            archive.addfile(info, io.BytesIO(payload))

    @staticmethod
    def read_jsonl(path):
        return [
            json.loads(line)
            for line in path.read_text(encoding="utf-8").splitlines()
        ]


if __name__ == "__main__":
    unittest.main()
