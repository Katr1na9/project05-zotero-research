import importlib.util
import unittest
from pathlib import Path


EXPERIMENT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = EXPERIMENT_DIR / "scripts" / "compile_pgdump_motifs.py"
SPEC = importlib.util.spec_from_file_location(
    "compile_pgdump_motifs",
    MODULE_PATH,
)
compiler = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(compiler)


class PgdumpMotifCompilerTests(unittest.TestCase):
    def test_network_motif_uses_resolved_endpoint_and_process(self):
        events = [
            {
                "src_node": "net-1",
                "operation": "EVENT_RECVFROM",
                "dst_node": "proc-1",
                "event_uuid": "event-1",
                "timestamp_nanos": 100,
            }
        ]
        nodes = {
            "net-1": {
                "node_type": "netflow",
                "src_addr": "10.0.0.5",
                "dst_addr": "208.203.20.42",
            },
            "proc-1": {
                "node_type": "subject",
                "path": "/usr/local/firefox",
                "cmd": "firefox",
            },
        }
        spec = {
            "case_id": "C07-test",
            "artifact_id": "test-events",
            "motifs": [
                {
                    "motif_id": "C07-EC-001",
                    "match": {
                        "event_type_in": ["EVENT_RECVFROM"],
                        "process_contains_any": ["firefox"],
                        "remote_ip_in": ["208.203.20.42"],
                    },
                    "claim": {"source_type": "network_summary"},
                }
            ],
        }

        claims, report = compiler.compile_motifs(events, nodes, spec)

        self.assertEqual(1, len(claims))
        self.assertEqual("event-1", claims[0]["source_pointer"]["record_id"])
        self.assertIn("representative_event_uuids=event-1", claims[0]["notes"])
        self.assertEqual(1, report["motifs"]["C07-EC-001"]["matched_event_count"])

    def test_file_motif_requires_the_resolved_path(self):
        event = {
            "src_node": "file-1",
            "operation": "EVENT_OPEN",
            "dst_node": "proc-1",
            "event_uuid": "event-2",
            "timestamp_nanos": 200,
        }
        nodes = {
            "file-1": {"node_type": "file", "path": "/var/log/sshdlog"},
            "proc-1": {"node_type": "subject", "path": "/usr/sbin/sshd", "cmd": ""},
        }
        self.assertTrue(
            compiler.matches_rule(
                compiler.event_context(event, nodes),
                {
                    "event_type_in": ["EVENT_OPEN"],
                    "process_contains_any": ["/usr/sbin/sshd"],
                    "path_contains_any": ["/var/log/sshdlog"],
                },
            )
        )

    def test_unmatched_motif_is_reported_but_not_emitted_as_a_claim(self):
        spec = {
            "case_id": "C07-test",
            "artifact_id": "test-events",
            "motifs": [
                {
                    "motif_id": "C07-EC-002",
                    "match": {"event_type_in": ["EVENT_EXECUTE"]},
                    "claim": {"source_type": "provenance_graph"},
                }
            ],
        }
        claims, report = compiler.compile_motifs([], {}, spec)
        self.assertEqual([], claims)
        self.assertEqual("not_observed", report["motifs"]["C07-EC-002"]["status"])


if __name__ == "__main__":
    unittest.main()
