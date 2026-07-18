import hashlib
import importlib.util
import json
import tempfile
import unittest
from datetime import datetime
from pathlib import Path


EXP = Path(__file__).resolve().parents[1]
SCRIPTS = EXP / "scripts"
ADAPTER_PATH = SCRIPTS / "recover_network_summary_adapter.py"


def load_adapter():
    spec = importlib.util.spec_from_file_location(
        "recover_network_summary_adapter", ADAPTER_PATH
    )
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


class RecoverNetworkSummaryAdapterTests(unittest.TestCase):
    def request(self):
        return {
            "case_id": "C02",
            "action_id": "C02-AA-003",
            "action_type": "recover_network_summary",
            "target": {
                "target_type": "case",
                "target_value": "R02 external endpoints",
            },
        }

    def fixture_nodes(self, root):
        nodes = root / "nodes.jsonl"
        node_bytes = write_jsonl(
            nodes,
            [
                {"record_type": "Subject", "node_uuid": "S0", "raw": {}},
                {
                    "record_type": "NetFlowObject",
                    "node_uuid": "NF-B",
                    "raw": {
                        "localAddress": "128.55.12.73",
                        "localPort": 50001,
                        "remoteAddress": "8.8.8.8",
                        "remotePort": 53,
                        "ipProtocol": None,
                    },
                },
                {
                    "record_type": "NetFlowObject",
                    "node_uuid": "NF-A",
                    "raw": {
                        "localAddress": "localhost",
                        "localPort": -1,
                        "remoteAddress": "8.8.8.8",
                        "remotePort": 53,
                        "ipProtocol": None,
                    },
                },
                {
                    "record_type": "NetFlowObject",
                    "node_uuid": "NF-D",
                    "raw": {
                        "localAddress": "10.0.0.1",
                        "localPort": 40001,
                        "remoteAddress": "198.51.100.9",
                        "remotePort": 443,
                        "ipProtocol": "TCP",
                    },
                },
                {
                    "record_type": "NetFlowObject",
                    "node_uuid": "NF-C",
                    "raw": {
                        "localAddress": "10.0.0.1",
                        "localPort": 40000,
                        "remoteAddress": "198.51.100.9",
                        "remotePort": 443,
                        "ipProtocol": "TCP",
                    },
                },
            ],
        )
        return nodes, node_bytes

    def test_case_target_summarizes_observed_remote_endpoints_without_external_inference(self):
        self.assertTrue(
            ADAPTER_PATH.is_file(),
            "recover_network_summary_adapter.py must provide the bounded R02 pilot",
        )
        adapter = load_adapter()
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            nodes, node_bytes = self.fixture_nodes(root)
            result = adapter.execute_case_target(
                self.request(), nodes, root / "observation"
            )

            self.assertEqual("completed", result["execution_status"])
            self.assertEqual(
                "partial_external_classification_unresolved",
                result["observation"]["requested_scope_status"],
            )
            self.assertEqual(
                "unresolved",
                result["observation"]["external_classification"]["status"],
            )
            self.assertIsNone(
                result["observation"]["external_classification"][
                    "external_endpoint_count"
                ]
            )
            self.assertEqual(4, result["observation"]["netflow_object_count"])
            self.assertEqual(
                2, result["observation"]["observed_remote_endpoint_count"]
            )
            self.assertEqual(
                2 * len(node_bytes),
                result["resource_trace"]["data_access"]["bytes_scanned"],
            )
            self.assertEqual(
                2 * 5,
                result["resource_trace"]["data_access"]["records_scanned"],
            )
            self.assertEqual(
                result["resource_trace"]["data_access"]["records_scanned"],
                result["primitive_operation_count"],
            )
            self.assertEqual(
                hashlib.sha256(node_bytes).hexdigest(),
                result["input_integrity"]["nodes"]["sha256"],
            )
            self.assertEqual(
                hashlib.sha256(ADAPTER_PATH.read_bytes()).hexdigest(),
                result["adapter_source"]["sha256"],
            )
            self.assertEqual(
                ADAPTER_PATH.resolve().as_posix(), result["adapter_source"]["path"]
            )
            started = datetime.fromisoformat(
                result["started_utc"].replace("Z", "+00:00")
            )
            ended = datetime.fromisoformat(result["ended_utc"].replace("Z", "+00:00"))
            self.assertLessEqual(started, ended)

            summary_path = root / "observation" / "observed-remote-endpoints.jsonl"
            summary_rows = [
                json.loads(line)
                for line in summary_path.read_text(encoding="utf-8").splitlines()
            ]
            self.assertEqual(
                [
                    {
                        "ip_protocol": "TCP",
                        "local_addresses": ["10.0.0.1"],
                        "local_ports": [40000, 40001],
                        "netflow_object_count": 2,
                        "remote_address": "198.51.100.9",
                        "remote_port": 443,
                        "source_node_uuids": ["NF-C", "NF-D"],
                        "unknown_local_port_count": 0,
                    },
                    {
                        "ip_protocol": None,
                        "local_addresses": ["128.55.12.73", "localhost"],
                        "local_ports": [50001],
                        "netflow_object_count": 2,
                        "remote_address": "8.8.8.8",
                        "remote_port": 53,
                        "source_node_uuids": ["NF-A", "NF-B"],
                        "unknown_local_port_count": 1,
                    },
                ],
                summary_rows,
            )
            self.assertEqual(
                hashlib.sha256(summary_path.read_bytes()).hexdigest(),
                result["observation"]["artifacts"]["remote_endpoints"]["sha256"],
            )

    def test_oracle_fields_are_rejected_before_any_observation_is_created(self):
        self.assertTrue(ADAPTER_PATH.is_file())
        adapter = load_adapter()
        request = self.request()
        request["recoverable_claim_ids"] = ["C05-EC-006"]
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            nodes, _ = self.fixture_nodes(root)
            output = root / "observation"
            with self.assertRaisesRegex(ValueError, "forbidden planner-oracle fields"):
                adapter.execute_case_target(request, nodes, output)
            self.assertFalse(output.exists())

    def test_non_allowlisted_case_target_is_rejected_without_output(self):
        self.assertTrue(ADAPTER_PATH.is_file())
        adapter = load_adapter()
        request = self.request()
        request["target"] = {
            "target_type": "endpoint",
            "target_value": "8.8.8.8:53",
        }
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            nodes, _ = self.fixture_nodes(root)
            output = root / "observation"
            with self.assertRaisesRegex(ValueError, "allow-listed R02 case target"):
                adapter.execute_case_target(request, nodes, output)
            self.assertFalse(output.exists())

    def test_node_source_split_merge_conserves_resources_summary_and_sha256(self):
        self.assertTrue(ADAPTER_PATH.is_file())
        adapter = load_adapter()
        self.assertTrue(hasattr(adapter, "execute_case_target_shards"))
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            nodes, _ = self.fixture_nodes(root)
            lines = nodes.read_bytes().splitlines(keepends=True)
            shard_a = root / "nodes-part-a.jsonl"
            shard_b = root / "nodes-part-b.jsonl"
            shard_a.write_bytes(b"".join(lines[:2]))
            shard_b.write_bytes(b"".join(lines[2:]))

            merged = adapter.execute_case_target(
                self.request(), nodes, root / "merged-observation"
            )
            split = adapter.execute_case_target_shards(
                self.request(), [shard_a, shard_b], root / "split-observation"
            )

            self.assertEqual(
                merged["resource_trace"]["data_access"],
                split["resource_trace"]["data_access"],
            )
            self.assertEqual(
                merged["primitive_operation_count"], split["primitive_operation_count"]
            )
            for field in ("netflow_object_count", "observed_remote_endpoint_count"):
                self.assertEqual(merged["observation"][field], split["observation"][field])
            self.assertEqual(
                merged["observation"]["artifacts"]["remote_endpoints"]["sha256"],
                split["observation"]["artifacts"]["remote_endpoints"]["sha256"],
            )

    def test_execution_result_writer_never_overwrites_a_prior_run(self):
        self.assertTrue(ADAPTER_PATH.is_file())
        adapter = load_adapter()
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            nodes, _ = self.fixture_nodes(root)
            result = adapter.execute_case_target(
                self.request(), nodes, root / "observation"
            )
            result_path = root / "pilot-run.json"
            adapter.write_execution_result(result_path, result)
            self.assertEqual(result, json.loads(result_path.read_text(encoding="utf-8")))
            with self.assertRaises(FileExistsError):
                adapter.write_execution_result(result_path, result)


if __name__ == "__main__":
    unittest.main()
