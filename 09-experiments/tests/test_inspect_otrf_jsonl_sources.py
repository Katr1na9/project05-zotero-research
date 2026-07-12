import importlib.util
import json
import tempfile
import unittest
import zipfile
from pathlib import Path


EXPERIMENT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = EXPERIMENT_DIR / "scripts" / "inspect_otrf_jsonl_sources.py"
SPEC = importlib.util.spec_from_file_location("inspect_otrf_sources", MODULE_PATH)
inspector = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(inspector)


class InspectOtrfSourcesTests(unittest.TestCase):
    def test_structural_scan_counts_hosts_without_copying_payloads(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            host_archive = root / "host.zip"
            host_rows = [
                {
                    "@timestamp": "2020-05-01T00:00:00Z",
                    "Hostname": "SCRANTON.example.test",
                    "Channel": "Sysmon",
                    "SourceName": "Provider-A",
                    "EventID": 1,
                    "Message": "sensitive payload one",
                },
                {
                    "@timestamp": "2020-05-01T00:01:00Z",
                    "Hostname": "NASHUA.example.test",
                    "Channel": "PowerShell",
                    "SourceName": "Provider-B",
                    "EventID": 4104,
                    "Message": "sensitive payload two",
                },
            ]
            with zipfile.ZipFile(host_archive, "w", zipfile.ZIP_DEFLATED) as archive:
                archive.writestr(
                    "events.json",
                    "".join(json.dumps(row) + "\n" for row in host_rows),
                )

            zeek_log = root / "zeek.log"
            zeek_log.write_text(
                json.dumps(
                    {
                        "@stream": "conn",
                        "ts": 1588291200.0,
                        "payload": "do not retain",
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            result = inspector.inspect_sources(
                host_archive,
                zeek_log,
                {"SCRANTON", "NASHUA"},
            )

        self.assertEqual(
            {"NASHUA": 1, "SCRANTON": 1},
            result["host_events"]["expected_host_rows"],
        )
        self.assertEqual(1, result["zeek_events"]["parsed_rows"])
        serialized = json.dumps(result)
        self.assertNotIn("sensitive payload", serialized)
        self.assertNotIn("do not retain", serialized)

    def test_malformed_rows_are_counted_without_content_retention(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            host_archive = root / "host.zip"
            with zipfile.ZipFile(host_archive, "w") as archive:
                archive.writestr("events.json", "not-json\n")
            zeek_log = root / "zeek.log"
            zeek_log.write_text("not-json\n", encoding="utf-8")

            result = inspector.inspect_sources(
                host_archive,
                zeek_log,
                {"SCRANTON"},
            )

        self.assertEqual(1, result["host_events"]["malformed_rows"])
        self.assertEqual(1, result["zeek_events"]["malformed_rows"])
        self.assertNotIn("not-json", json.dumps(result))


if __name__ == "__main__":
    unittest.main()
