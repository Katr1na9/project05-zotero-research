import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


EXP = Path(__file__).resolve().parents[1]
SCRIPTS = EXP / "scripts"
BUILDER_PATH = SCRIPTS / "build_capability_pilot_measurement_v03.py"


def load_builder():
    spec = importlib.util.spec_from_file_location(
        "build_capability_pilot_measurement_v03", BUILDER_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CapabilityPilotMeasurementTests(unittest.TestCase):
    def result(self):
        return {
            "invocation": {
                "case_id": "C02",
                "action_id": "C02-AA-002",
                "action_type": "query_host_subgraph",
                "target": {"target_type": "file", "target_value": "/tmp/vUgefal"},
            },
            "started_utc": "2026-07-18T06:36:07.155968Z",
            "ended_utc": "2026-07-18T06:36:16.037496Z",
            "execution_status": "completed",
            "termination_reason": "collector_completed",
            "primitive_operation_count": 807514,
            "resource_trace": {
                "analyst_time_by_role": [],
                "compute": {
                    "wall_seconds": 8.88,
                    "cpu_seconds": 8.75,
                    "memory_byte_seconds": 210473890.34,
                },
                "data_access": {"bytes_scanned": 901652996, "records_scanned": 807514},
                "direct_currency": {"amount": 0.0, "currency": "CNY"},
                "authorization_wait_seconds": 0.0,
                "shared_overhead": {
                    "setup_seconds": 0.0,
                    "allocation_status": "unallocated",
                    "allocation_rule": None,
                },
            },
            "observation": {
                "subgraph_event_count": 3002,
                "subgraph_node_count": 1391,
                "evidence_perturbations": [],
                "downtime_seconds": 0.0,
            },
        }

    def schedule_row(self):
        return {
            "scheduled_run_index": "17",
            "phase": "calibration",
            "attempt_round": "1",
            "block_id": "calibration-round-01",
            "case_id": "C02",
            "action_id": "C02-AA-002",
        }

    def test_converter_marks_a_real_pilot_as_noncoverage_capability_evidence(self):
        self.assertTrue(
            BUILDER_PATH.is_file(),
            "capability pilot measurements must be explicitly transformed and labelled",
        )
        builder = load_builder()
        record = builder.build_measurement_record(
            self.result(),
            [self.schedule_row()],
            scheduled_run_index=17,
            machine_id="machine-pseudonym-01",
            environment_id="windows-local-python311",
            initial_state_id="uncontrolled-local-file-state",
        )

        self.assertEqual("C02", record["case_id"])
        self.assertEqual("C02-AA-002", record["action_id"])
        self.assertEqual("calibration", record["phase"])
        self.assertEqual(807514, record["primitive_operation_count"])
        self.assertEqual(self.result()["resource_trace"], record["resource_trace"])
        self.assertEqual(4393, record["observation_summary"]["returned_evidence_count"])
        self.assertFalse(record["context_covariates"]["initial_state_reset"])
        self.assertEqual(
            "unscheduled_capability_pilot",
            record["randomization_deviation"]["deviation_type"],
        )
        self.assertNotIn("cost", record)
        self.assertNotIn("recoverable_claim_ids", record)

        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "capability-pilot-record.json"
            builder.write_measurement_source(path, record)
            self.assertEqual([record], json.loads(path.read_text(encoding="utf-8")))
            with self.assertRaises(FileExistsError):
                builder.write_measurement_source(path, record)

    def test_converter_counts_network_summary_endpoints_as_returned_evidence(self):
        builder = load_builder()
        pilot = self.result()
        pilot["invocation"] = {
            "case_id": "C02",
            "action_id": "C02-AA-003",
            "action_type": "recover_network_summary",
            "target": {
                "target_type": "case",
                "target_value": "R02 external endpoints",
            },
        }
        pilot["observation"] = {
            "schema_id": "project05-cdm18-observed-remote-endpoint-summary-v0.1",
            "observed_remote_endpoint_count": 143,
            "requested_scope_status": "partial_external_classification_unresolved",
            "evidence_perturbations": [],
            "downtime_seconds": 0.0,
        }
        schedule = self.schedule_row()
        schedule["action_id"] = "C02-AA-003"

        record = builder.build_measurement_record(
            pilot,
            [schedule],
            scheduled_run_index=17,
            machine_id="machine-pseudonym-01",
            environment_id="windows-local-python311",
            initial_state_id="uncontrolled-local-file-state",
        )

        self.assertEqual(143, record["observation_summary"]["returned_evidence_count"])


if __name__ == "__main__":
    unittest.main()
