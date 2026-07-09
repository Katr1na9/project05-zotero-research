import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


EXPERIMENT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = EXPERIMENT_DIR / "scripts" / "compile_real_motifs.py"


def load_compiler():
    if not MODULE_PATH.exists():
        return None
    spec = importlib.util.spec_from_file_location(
        "compile_real_motifs",
        MODULE_PATH,
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


compiler = load_compiler()


class RealMotifCompilerTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(
            compiler,
            "compile_real_motifs.py has not been implemented",
        )

    def test_compiles_auditable_network_behavior_motif(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            nodes_path = root / "nodes.jsonl"
            events_path = root / "events.jsonl"
            self.write_jsonl(
                nodes_path,
                [
                    {
                        "record_type": "NetFlowObject",
                        "node_uuid": "net-1",
                        "raw": {
                            "uuid": "net-1",
                            "remoteAddress": "203.0.113.7",
                            "remotePort": 443,
                        },
                    }
                ],
            )
            self.write_jsonl(
                events_path,
                [
                    {
                        "event_uuid": "event-1",
                        "timestamp_nanos": 150,
                        "event_type": "EVENT_CONNECT",
                        "subject_uuid": "subject-1",
                        "predicate_object_uuid": "net-1",
                        "raw": {
                            "properties": {
                                "map": {"exec": "firefox.exe"}
                            }
                        },
                    },
                    {
                        "event_uuid": "event-2",
                        "timestamp_nanos": 200,
                        "event_type": "EVENT_READ",
                        "subject_uuid": "subject-1",
                        "predicate_object_uuid": "file-1",
                        "raw": {
                            "properties": {
                                "map": {"exec": "firefox.exe"}
                            }
                        },
                    },
                ],
            )
            spec = {
                "case_id": "C99-real-fixture",
                "artifact_id": "fixture_events",
                "motifs": [
                    {
                        "motif_id": "C99-EC-001",
                        "match": {
                            "event_type_in": ["EVENT_CONNECT"],
                            "process_in": ["firefox.exe"],
                            "remote_ip_in": ["203.0.113.7"],
                        },
                        "claim": {
                            "source_type": "network_summary",
                            "claim_type": "network_connection",
                            "subject": {
                                "entity_type": "process",
                                "value": "firefox.exe",
                            },
                            "predicate": "connected_to",
                            "object": {
                                "entity_type": "ip",
                                "value": "203.0.113.7",
                            },
                            "observable_status": "visible",
                            "tags": [
                                "hideable",
                                "real_cdm",
                                "stage:command_and_control",
                                "node:N01_c2",
                            ],
                        },
                    }
                ],
            }

            claims, report = compiler.compile_motifs(
                events_path,
                nodes_path,
                spec,
            )

        self.assertEqual(1, len(claims))
        self.assertEqual("C99-EC-001", claims[0]["claim_id"])
        self.assertEqual("event-1", claims[0]["source_pointer"]["record_id"])
        self.assertIn("matched_event_count=1", claims[0]["notes"])
        self.assertIn("representative_event_uuids=event-1", claims[0]["notes"])
        self.assertEqual(
            ["event-1"],
            report["motifs"]["C99-EC-001"]["representative_event_uuids"],
        )

    @staticmethod
    def write_jsonl(path, records):
        path.write_text(
            "".join(
                json.dumps(record) + "\n"
                for record in records
            ),
            encoding="utf-8",
        )


if __name__ == "__main__":
    unittest.main()
