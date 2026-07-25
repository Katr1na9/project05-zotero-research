import csv
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


EXP = Path(__file__).resolve().parents[1]
SCRIPTS = EXP / "scripts"
ONTOLOGY = (
    EXP
    / "governance"
    / "profiles"
    / "action-ontology-v0.3-real-only-draft.json"
)


def load_script(name):
    path = SCRIPTS / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"test_{name}", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


SCHEDULER = load_script("build_operational_cost_schedule_v03")
IMPORTER = load_script("import_operational_cost_measurements_v03")
VALIDATOR = load_script("validate_operational_cost_measurements_v03")


class OperationalCostV03Tests(unittest.TestCase):
    def build_protocol(self, root):
        output = root / "governance"
        SCHEDULER.build_outputs(
            ONTOLOGY,
            output,
            seed=20260718,
            minimum_attempt_rounds=3,
        )
        protocol = output / SCHEDULER.PROTOCOL_FILENAME
        schedule = output / SCHEDULER.SCHEDULE_FILENAME
        with schedule.open("r", encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        return protocol, schedule, rows

    def record(self, schedule_row):
        return {
            "measurement_id": f"measurement--{schedule_row['planned_execution_attempt_id']}",
            "case_id": schedule_row["case_id"],
            "action_id": schedule_row["action_id"],
            "phase": schedule_row["phase"],
            "planner_decision_id": schedule_row["planned_planner_decision_id"],
            "execution_attempt_id": schedule_row["planned_execution_attempt_id"],
            "retry_of_attempt_id": None,
            "attempt_round": int(schedule_row["attempt_round"]),
            "scheduled_run_index": int(schedule_row["scheduled_run_index"]),
            "block_id": schedule_row["block_id"],
            "randomization_deviation": None,
            "started_utc": "2026-07-18T01:00:00Z",
            "ended_utc": "2026-07-18T01:00:05Z",
            "execution_status": "completed",
            "termination_reason": "collector_completed",
            "primitive_operation_count": 4,
            "resource_trace": {
                "analyst_time_by_role": [
                    {"role": "forensic_analyst", "seconds": 12.5}
                ],
                "compute": {
                    "wall_seconds": 5.0,
                    "cpu_seconds": 3.5,
                    "memory_byte_seconds": 1024.0,
                },
                "data_access": {
                    "bytes_scanned": 4096,
                    "records_scanned": 32,
                },
                "direct_currency": {"amount": 0.0, "currency": "CNY"},
                "authorization_wait_seconds": 0.0,
                "shared_overhead": {
                    "setup_seconds": 1.0,
                    "allocation_status": "unallocated",
                    "allocation_rule": None,
                },
            },
            "context_covariates": {
                "host_count": 1,
                "retention_window_days": 7.0,
                "authorization": {
                    "required": False,
                    "boundary": "none",
                    "approval_reference": None,
                },
                "machine_id": "machine-test-01",
                "cache_state": "controlled",
                "executor_id": "executor-test-01",
                "execution_date": "2026-07-18",
                "environment_id": "env-test-01",
                "initial_state_id": "state-test-01",
                "initial_state_reset": True,
            },
            "hard_constraints": {
                "authorization_satisfied": True,
                "data_available": True,
                "safety_gate_passed": True,
                "violations": [],
            },
            "observation_summary": {
                "returned_evidence_count": 2,
                "evidence_perturbations": [],
                "downtime_seconds": 0.0,
            },
        }

    def import_records(self, root, protocol, records):
        input_dir = root / "input"
        input_dir.mkdir()
        source = input_dir / "telemetry.json"
        source.write_text(json.dumps(records), encoding="utf-8")
        output = root / "output"
        IMPORTER.import_measurements(
            input_dir,
            output,
            protocol,
            "2026-07-18T02:00:00Z",
        )
        report = json.loads(
            (output / "measurement_validation_report_v0.3.json").read_text(
                encoding="utf-8"
            )
        )
        return source, output, report

    def test_schedule_is_seeded_blocked_and_covers_each_action_three_times(self):
        ontology = json.loads(ONTOLOGY.read_text(encoding="utf-8"))
        first = SCHEDULER.build_schedule(ontology, 20260718, 3)
        second = SCHEDULER.build_schedule(ontology, 20260718, 3)

        self.assertEqual(first, second)
        self.assertEqual(150, len(first))
        self.assertEqual(57, sum(row["phase"] == "calibration" for row in first))
        self.assertEqual(93, sum(row["phase"] == "development" for row in first))
        counts = {}
        for row in first:
            key = (row["case_id"], row["action_id"])
            counts[key] = counts.get(key, 0) + 1
        self.assertEqual({3}, set(counts.values()))
        calibration_round_1 = [
            row["action_id"]
            for row in first
            if row["phase"] == "calibration" and row["attempt_round"] == 1
        ]
        calibration_round_2 = [
            row["action_id"]
            for row in first
            if row["phase"] == "calibration" and row["attempt_round"] == 2
        ]
        self.assertNotEqual(calibration_round_1, calibration_round_2)

    def test_complete_attempt_is_valid_but_one_attempt_does_not_pass_coverage(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            protocol, _, rows = self.build_protocol(root)
            _, _, report = self.import_records(root, protocol, [self.record(rows[0])])

            self.assertEqual("passed", report["validation_status"])
            self.assertTrue(report["schema_valid"])
            self.assertTrue(report["provenance_valid"])
            self.assertTrue(report["resource_trace_complete"])
            self.assertTrue(report["action_executor_registry_integrity_valid"])
            self.assertFalse(report["execution_authorized"])
            self.assertEqual(1, report["planner_decision_count"])
            self.assertEqual(1, report["execution_attempt_count"])
            self.assertEqual(4, report["primitive_operation_count"])
            self.assertFalse(report["coverage_gate_passed"])
            self.assertFalse(report["statistical_sufficiency_established"])
            self.assertFalse(report["formal_measured_cost_profile_ready"])
            self.assertIn(
                "action_executor_registry_not_frozen_or_execution_authorized",
                report["blocking_reasons"],
            )

    def test_retry_counts_as_execution_attempt_not_independent_coverage_replicate(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            protocol, _, rows = self.build_protocol(root)
            primary = self.record(rows[0])
            primary["execution_status"] = "failed"
            primary["termination_reason"] = "collector_error"
            retry = json.loads(json.dumps(primary))
            retry["measurement_id"] += "--retry"
            retry["execution_attempt_id"] += "--retry"
            retry["retry_of_attempt_id"] = primary["execution_attempt_id"]
            retry["execution_status"] = "completed"
            retry["termination_reason"] = "collector_completed_after_retry"
            retry["primitive_operation_count"] = 3

            _, _, report = self.import_records(root, protocol, [primary, retry])

            self.assertEqual("passed", report["validation_status"])
            self.assertEqual(1, report["planner_decision_count"])
            self.assertEqual(2, report["execution_attempt_count"])
            self.assertEqual(1, report["retry_attempt_count"])
            self.assertEqual(7, report["primitive_operation_count"])
            self.assertEqual(0, report["covered_action_count"])

    def test_full_fake_coverage_cannot_bypass_unimplemented_executor_gate(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            protocol, _, rows = self.build_protocol(root)
            records = [self.record(row) for row in rows]

            _, _, report = self.import_records(root, protocol, records)

            self.assertEqual("passed", report["validation_status"])
            self.assertTrue(report["coverage_gate_passed"])
            self.assertTrue(report["resource_trace_complete"])
            self.assertFalse(report["execution_authorized"])
            self.assertFalse(report["measurement_batch_ready"])
            self.assertFalse(report["formal_measured_cost_profile_ready"])

    def test_capability_pilot_is_not_reported_as_formal_measurement_availability(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            protocol, _, rows = self.build_protocol(root)
            pilot = self.record(rows[0])
            pilot["randomization_deviation"] = {
                "deviation_type": "unscheduled_capability_pilot",
                "reason": "adapter capability evidence only",
                "adjudication_status": "accepted",
            }
            pilot["context_covariates"]["initial_state_reset"] = False
            input_dir = root / "input"
            input_dir.mkdir()
            (input_dir / "pilot.json").write_text(json.dumps([pilot]), encoding="utf-8")

            manifest = IMPORTER.import_measurements(
                input_dir,
                root / "output",
                protocol,
                "2026-07-18T02:00:00Z",
            )

            self.assertEqual(
                "capability_pilot_only_not_formal_schedule_measurement",
                manifest["real_measurement_status"],
            )
            self.assertFalse(manifest["measurement_batch_ready"])

    def test_missing_unit_measurement_is_audited_without_inventing_a_value(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            protocol, _, rows = self.build_protocol(root)
            record = self.record(rows[0])
            record["resource_trace"]["compute"]["memory_byte_seconds"] = None

            _, _, report = self.import_records(root, protocol, [record])

            self.assertEqual("passed", report["validation_status"])
            self.assertFalse(report["resource_trace_complete"])
            self.assertIn(
                "unit_bearing_resource_trace_incomplete", report["blocking_reasons"]
            )
            missing = report["resource_incomplete_attempts"][
                record["execution_attempt_id"]
            ]
            self.assertIn("resource_trace/compute/memory_byte_seconds", missing)

    def test_context_scale_is_not_misclassified_as_resource_consumption(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            protocol, _, rows = self.build_protocol(root)
            record = self.record(rows[0])

            self.assertIn("host_count", record["context_covariates"])
            self.assertIn("retention_window_days", record["context_covariates"])
            self.assertNotIn("host_count", record["resource_trace"])
            self.assertNotIn("retention_window_days", record["resource_trace"])

    def test_tampered_raw_source_breaks_replayable_provenance(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            protocol, _, rows = self.build_protocol(root)
            source, output, _ = self.import_records(
                root, protocol, [self.record(rows[0])]
            )
            source.write_text("[]", encoding="utf-8")

            report = VALIDATOR.validate_batch(
                output / "operational_cost_measurements_v0.3.json"
            )

            self.assertFalse(report["provenance_valid"])
            self.assertTrue(
                any("source file sha256 mismatch" in error for error in report["semantic_errors"])
            )


if __name__ == "__main__":
    unittest.main()
