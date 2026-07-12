import importlib.util
import json
import tempfile
import unittest
import zipfile
from pathlib import Path


EXPERIMENT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = EXPERIMENT_DIR / "scripts" / "probe_otrf_motifs.py"
SPEC = importlib.util.spec_from_file_location("probe_otrf_motifs", MODULE_PATH)
probe = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(probe)


class ProbeOtrfMotifsTests(unittest.TestCase):
    def test_gate_counts_provider_families_not_event_types(self):
        spec = {
            "case_id": "RXX",
            "spec_version": "test",
            "host_archive_member": "events.json",
            "searchable_fields": ["Message"],
            "nodes": [
                {
                    "node_id": "N01",
                    "critical": True,
                    "expected_hosts": ["SCRANTON"],
                    "anchors": [{"anchor_id": "a1", "terms": ["alpha"]}],
                    "minimum_distinct_provider_families": 2,
                },
                {
                    "node_id": "N02",
                    "critical": True,
                    "expected_hosts": ["SCRANTON"],
                    "anchors": [{"anchor_id": "a2", "terms": ["beta"]}],
                    "minimum_distinct_provider_families": 2,
                },
            ],
            "gate": {"minimum_passing_critical_nodes": 1},
        }
        rows = [
            {
                "@timestamp": "2020-01-01T00:00:00Z",
                "Hostname": "SCRANTON.example",
                "Channel": "Microsoft-Windows-Sysmon/Operational",
                "SourceName": "Microsoft-Windows-Sysmon",
                "EventID": 1,
                "RecordNumber": 1,
                "Message": "alpha",
                "Secret": "unrelated-secret",
            },
            {
                "@timestamp": "2020-01-01T00:00:01Z",
                "Hostname": "SCRANTON.example",
                "Channel": "Microsoft-Windows-Sysmon/Operational",
                "SourceName": "Microsoft-Windows-Sysmon",
                "EventID": 11,
                "RecordNumber": 2,
                "Message": "alpha",
            },
            {
                "@timestamp": "2020-01-01T00:00:02Z",
                "Hostname": "SCRANTON.example",
                "Channel": "Microsoft-Windows-PowerShell/Operational",
                "SourceName": "Microsoft-Windows-PowerShell",
                "EventID": 4104,
                "RecordNumber": 3,
                "Message": "alpha",
            },
            {
                "@timestamp": "2020-01-01T00:00:03Z",
                "Hostname": "SCRANTON.example",
                "Channel": "Microsoft-Windows-Sysmon/Operational",
                "SourceName": "Microsoft-Windows-Sysmon",
                "EventID": 1,
                "RecordNumber": 4,
                "Message": "beta",
            },
        ]

        with tempfile.TemporaryDirectory() as temp_dir:
            archive_path = Path(temp_dir) / "events.zip"
            with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as archive:
                archive.writestr(
                    "events.json",
                    "".join(json.dumps(row) + "\n" for row in rows),
                )
            result = probe.probe_archive(archive_path, spec)

        by_node = {node["node_id"]: node for node in result["nodes"]}
        self.assertEqual(["powershell", "sysmon"], by_node["N01"]["counted_provider_families"])
        self.assertTrue(by_node["N01"]["multiclaim_node_pass"])
        self.assertEqual(
            {
                "a1|powershell": 1,
                "a1|sysmon": 2,
            },
            by_node["N01"]["anchor_provider_family_counts"],
        )
        self.assertEqual(
            2,
            len(by_node["N01"]["representative_by_anchor_provider_family"]),
        )
        self.assertFalse(by_node["N02"]["multiclaim_node_pass"])
        self.assertEqual("PASS", result["d3_multiclaim_gate"])
        self.assertNotIn("unrelated-secret", json.dumps(result))

    def test_host_filter_prevents_cross_host_anchor_leakage(self):
        spec = {
            "case_id": "RXX",
            "spec_version": "test",
            "host_archive_member": "events.json",
            "searchable_fields": ["Message"],
            "nodes": [
                {
                    "node_id": "N01",
                    "critical": True,
                    "expected_hosts": ["SCRANTON"],
                    "anchors": [{"anchor_id": "a1", "terms": ["alpha"]}],
                    "minimum_distinct_provider_families": 1,
                }
            ],
            "gate": {"minimum_passing_critical_nodes": 1},
        }
        row = {
            "Hostname": "NASHUA.example",
            "Channel": "Microsoft-Windows-Sysmon/Operational",
            "SourceName": "Microsoft-Windows-Sysmon",
            "EventID": 1,
            "RecordNumber": 1,
            "Message": "alpha",
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            archive_path = Path(temp_dir) / "events.zip"
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.writestr("events.json", json.dumps(row) + "\n")
            result = probe.probe_archive(archive_path, spec)

        self.assertEqual("FAIL", result["d3_multiclaim_gate"])
        self.assertEqual(0, result["nodes"][0]["matched_record_count"])


if __name__ == "__main__":
    unittest.main()
