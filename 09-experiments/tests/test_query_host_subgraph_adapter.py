import hashlib
import importlib.util
import json
import tempfile
import unittest
from datetime import datetime
from pathlib import Path


EXP = Path(__file__).resolve().parents[1]
SCRIPTS = EXP / "scripts"
ADAPTER_PATH = SCRIPTS / "query_host_subgraph_adapter.py"


def load_adapter():
    spec = importlib.util.spec_from_file_location("query_host_subgraph_adapter", ADAPTER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_jsonl(path, rows):
    payload = b"".join(
        json.dumps(row, sort_keys=True, separators=(",", ":")).encode("utf-8") + b"\n"
        for row in rows
    )
    path.write_bytes(payload)
    return payload


class QueryHostSubgraphAdapterTests(unittest.TestCase):
    def request(self):
        return {
            "case_id": "C02",
            "action_id": "C02-AA-002",
            "action_type": "query_host_subgraph",
            "target": {"target_type": "file", "target_value": "/tmp/vUgefal"},
        }

    def fixture_paths(self, root):
        events = root / "events.jsonl"
        nodes = root / "nodes.jsonl"
        event_bytes = write_jsonl(
            events,
            [
                {
                    "event_uuid": "E0",
                    "subject_uuid": "S0",
                    "predicate_object_uuid": "O0",
                    "predicate_object_2_uuid": None,
                    "raw": {"predicateObjectPath": None, "predicateObject2Path": None},
                },
                {
                    "event_uuid": "E1",
                    "subject_uuid": "S1",
                    "predicate_object_uuid": "F1",
                    "predicate_object_2_uuid": None,
                    "raw": {
                        "predicateObjectPath": {"string": "/tmp/vUgefal"},
                        "predicateObject2Path": None,
                    },
                },
                {
                    "event_uuid": "E2",
                    "subject_uuid": "S1",
                    "predicate_object_uuid": "O2",
                    "predicate_object_2_uuid": None,
                    "raw": {"predicateObjectPath": None, "predicateObject2Path": None},
                },
                {
                    "event_uuid": "E3",
                    "subject_uuid": "S3",
                    "predicate_object_uuid": "O3",
                    "predicate_object_2_uuid": None,
                    "raw": {"predicateObjectPath": None, "predicateObject2Path": None},
                },
            ],
        )
        node_bytes = write_jsonl(
            nodes,
            [
                {"node_uuid": "S1", "record_type": "Subject"},
                {"node_uuid": "F1", "record_type": "FileObject"},
                {"node_uuid": "O2", "record_type": "FileObject"},
                {"node_uuid": "S0", "record_type": "Subject"},
                {"node_uuid": "O0", "record_type": "FileObject"},
            ],
        )
        return events, nodes, event_bytes, node_bytes

    def test_file_target_adapter_extracts_one_hop_subgraph_and_counts_raw_line_reads(self):
        self.assertTrue(
            ADAPTER_PATH.is_file(),
            "query_host_subgraph_adapter.py must provide the file-target pilot executor",
        )
        adapter = load_adapter()
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            events, nodes, event_bytes, node_bytes = self.fixture_paths(root)
            result = adapter.execute_file_target(
                self.request(), events, nodes, root / "observation"
            )

            self.assertEqual("completed", result["execution_status"])
            self.assertIn("adapter_source", result)
            self.assertEqual(
                hashlib.sha256(ADAPTER_PATH.read_bytes()).hexdigest(),
                result["adapter_source"]["sha256"],
            )
            self.assertEqual(
                ADAPTER_PATH.resolve().as_posix(), result["adapter_source"]["path"]
            )
            self.assertIn("started_utc", result)
            self.assertIn("ended_utc", result)
            started = datetime.fromisoformat(result["started_utc"].replace("Z", "+00:00"))
            ended = datetime.fromisoformat(result["ended_utc"].replace("Z", "+00:00"))
            self.assertLessEqual(started, ended)
            self.assertEqual(1, result["observation"]["target_match_event_count"])
            self.assertEqual(2, result["observation"]["subgraph_event_count"])
            self.assertEqual(3, result["observation"]["subgraph_node_count"])
            self.assertEqual(
                3 * len(event_bytes) + 2 * len(node_bytes),
                result["resource_trace"]["data_access"]["bytes_scanned"],
            )
            self.assertEqual(
                3 * 4 + 2 * 5,
                result["resource_trace"]["data_access"]["records_scanned"],
            )
            self.assertEqual(
                result["resource_trace"]["data_access"]["records_scanned"],
                result["primitive_operation_count"],
            )
            self.assertGreaterEqual(result["resource_trace"]["compute"]["wall_seconds"], 0.0)
            self.assertGreaterEqual(result["resource_trace"]["compute"]["cpu_seconds"], 0.0)
            self.assertGreaterEqual(
                result["resource_trace"]["compute"]["memory_byte_seconds"], 0.0
            )
            self.assertEqual(
                hashlib.sha256(event_bytes).hexdigest(),
                result["input_integrity"]["events"]["sha256"],
            )
            self.assertEqual(
                hashlib.sha256(node_bytes).hexdigest(),
                result["input_integrity"]["nodes"]["sha256"],
            )
            observed_events = [
                json.loads(line)["event_uuid"]
                for line in (root / "observation" / "subgraph-events.jsonl")
                .read_text(encoding="utf-8")
                .splitlines()
            ]
            observed_nodes = [
                json.loads(line)["node_uuid"]
                for line in (root / "observation" / "subgraph-nodes.jsonl")
                .read_text(encoding="utf-8")
                .splitlines()
            ]
            self.assertEqual(["E1", "E2"], observed_events)
            self.assertEqual(["S1", "F1", "O2"], observed_nodes)

    def test_source_oracle_fields_are_rejected_at_the_adapter_boundary(self):
        self.assertTrue(ADAPTER_PATH.is_file())
        adapter = load_adapter()
        request = self.request()
        request["recoverable_claim_ids"] = ["C05-EC-003"]
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            events, nodes, _, _ = self.fixture_paths(root)
            with self.assertRaisesRegex(ValueError, "forbidden planner-oracle fields"):
                adapter.execute_file_target(request, events, nodes, root / "observation")

    def test_non_file_targets_are_rejected_without_creating_an_observation(self):
        self.assertTrue(ADAPTER_PATH.is_file())
        adapter = load_adapter()
        request = self.request()
        request["target"] = {"target_type": "host", "target_value": "CADETS"}
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            events, nodes, _, _ = self.fixture_paths(root)
            output = root / "observation"
            with self.assertRaisesRegex(ValueError, "file target"):
                adapter.execute_file_target(request, events, nodes, output)
            self.assertFalse(output.exists())

    def test_execution_result_writer_persists_telemetry_without_overwriting_a_prior_run(self):
        self.assertTrue(ADAPTER_PATH.is_file())
        adapter = load_adapter()
        self.assertTrue(
            hasattr(adapter, "write_execution_result"),
            "the pilot must persist its telemetry as an immutable run record",
        )
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            events, nodes, _, _ = self.fixture_paths(root)
            result = adapter.execute_file_target(
                self.request(), events, nodes, root / "observation"
            )
            result_path = root / "pilot-result.json"
            adapter.write_execution_result(result_path, result)

            self.assertEqual(result, json.loads(result_path.read_text(encoding="utf-8")))
            with self.assertRaises(FileExistsError):
                adapter.write_execution_result(result_path, result)

    def test_event_source_split_merge_conserves_raw_resources_and_derived_artifacts(self):
        self.assertTrue(ADAPTER_PATH.is_file())
        adapter = load_adapter()
        self.assertTrue(
            hasattr(adapter, "execute_file_target_shards"),
            "one logical file-target action must support ordered event shards without repeated node scans",
        )
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            events, nodes, _, _ = self.fixture_paths(root)
            event_lines = events.read_bytes().splitlines(keepends=True)
            shard_a = root / "events-part-a.jsonl"
            shard_b = root / "events-part-b.jsonl"
            shard_a.write_bytes(b"".join(event_lines[:2]))
            shard_b.write_bytes(b"".join(event_lines[2:]))

            merged = adapter.execute_file_target(
                self.request(), events, nodes, root / "merged-observation"
            )
            split = adapter.execute_file_target_shards(
                self.request(), [shard_a, shard_b], nodes, root / "split-observation"
            )

            self.assertEqual(
                merged["resource_trace"]["data_access"],
                split["resource_trace"]["data_access"],
            )
            self.assertEqual(
                merged["primitive_operation_count"], split["primitive_operation_count"]
            )
            for field in (
                "target_match_event_count",
                "seed_node_count",
                "subgraph_event_count",
                "subgraph_node_count",
            ):
                self.assertEqual(merged["observation"][field], split["observation"][field])
            self.assertEqual(
                merged["observation"]["artifacts"]["events"]["sha256"],
                split["observation"]["artifacts"]["events"]["sha256"],
            )
            self.assertEqual(
                merged["observation"]["artifacts"]["nodes"]["sha256"],
                split["observation"]["artifacts"]["nodes"]["sha256"],
            )


if __name__ == "__main__":
    unittest.main()
