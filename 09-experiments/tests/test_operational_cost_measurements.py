import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
EXP = ROOT / "09-experiments"


def load_script(name):
    path = EXP / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"test_{name}", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


IMPORTER = load_script("import_operational_cost_measurements")
VALIDATOR = load_script("validate_operational_cost_measurements")


class OperationalCostMeasurementTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.case_dirs = VALIDATOR.discover_case_dirs(EXP / "examples", EXP / "real_cases")
        cls.first_case = cls.case_dirs[0]
        cls.config = json.loads((cls.first_case / "case_config.json").read_text(encoding="utf-8"))
        cls.action = json.loads((cls.first_case / "acquisition_actions.json").read_text(encoding="utf-8"))[0]

    def record(self):
        return {
            "measurement_id": "M-001",
            "case_id": self.config["case_id"],
            "action_id": self.action["action_id"],
            "attempt_id": "attempt-001",
            "started_utc": "2026-07-14T08:00:00Z",
            "ended_utc": "2026-07-14T08:02:00Z",
            "analyst_seconds": 45.0,
            "compute_seconds": 75.0,
            "records_scanned": 128,
            "bytes_scanned": 1024,
            "host_count": 1,
            "retention_window_days": 7.0,
            "authorization": {
                "required": True,
                "boundary": "host",
                "approval_reference": "AUTH-001",
            },
            "system_perturbation_events": 0,
            "execution_status": "completed",
            "collector": "project05-telemetry-exporter",
            "source_system": "test-harness",
        }

    def test_empty_import_builds_infrastructure_but_keeps_real_measurements_blocked(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest = IMPORTER.import_measurements(
                root / "empty", root / "out", self.case_dirs, "2026-07-14T08:00:00Z"
            )
            report = json.loads((root / "out" / "measurement_validation_report.json").read_text(encoding="utf-8"))
            self.assertEqual("implemented", manifest["infrastructure_status"])
            self.assertEqual("blocked_no_real_measurements", manifest["real_measurement_status"])
            self.assertEqual(0, report["record_count"])
            self.assertEqual(72, report["expected_action_count"])
            self.assertFalse(report["formal_measured_cost_profile_ready"])
            self.assertIn("no_real_operational_measurement_records", report["blocking_reasons"])

    def test_import_validates_time_bytes_hosts_retention_auth_and_provenance(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "in" / "telemetry.jsonl"
            source.parent.mkdir()
            source.write_text(json.dumps(self.record()) + "\n", encoding="utf-8")
            IMPORTER.import_measurements(
                source.parent, root / "out", self.case_dirs, "2026-07-14T08:00:00Z"
            )
            report = json.loads((root / "out" / "measurement_validation_report.json").read_text(encoding="utf-8"))
            batch = json.loads((root / "out" / "operational_cost_measurements.json").read_text(encoding="utf-8"))
            self.assertEqual("passed", report["validation_status"])
            self.assertTrue(report["schema_valid"])
            self.assertTrue(report["provenance_valid"])
            self.assertEqual(0, report["covered_action_count"])
            self.assertEqual(1, report["completed_attempt_count"])
            self.assertEqual(64, len(batch["records"][0]["source_file_sha256"]))
            self.assertEqual(64, len(batch["records"][0]["record_sha256"]))
            self.assertEqual("0.2.0", batch["version"])
            self.assertEqual(
                3,
                batch["measurement_protocol"][
                    "minimum_completed_attempts_per_action"
                ],
            )
            self.assertFalse(report["measurement_batch_ready"])

    def test_required_authorization_without_reference_fails_semantics(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            record = self.record()
            record["authorization"]["approval_reference"] = None
            source = root / "in" / "telemetry.json"
            source.parent.mkdir()
            source.write_text(json.dumps([record]), encoding="utf-8")
            IMPORTER.import_measurements(
                source.parent, root / "out", self.case_dirs, "2026-07-14T08:00:00Z"
            )
            report = json.loads((root / "out" / "measurement_validation_report.json").read_text(encoding="utf-8"))
            self.assertEqual("failed", report["validation_status"])
            self.assertTrue(any("approval_reference" in error for error in report["semantic_errors"]))

    def test_failed_attempt_is_audited_but_does_not_count_as_coverage(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            record = self.record()
            record["execution_status"] = "failed"
            source = root / "in" / "telemetry.json"
            source.parent.mkdir()
            source.write_text(json.dumps([record]), encoding="utf-8")

            IMPORTER.import_measurements(
                source.parent, root / "out", self.case_dirs, "2026-07-14T08:00:00Z"
            )
            report = json.loads(
                (root / "out" / "measurement_validation_report.json").read_text(
                    encoding="utf-8"
                )
            )

            self.assertEqual(1, report["record_count"])
            self.assertEqual(0, report["covered_action_count"])
            self.assertEqual(0, report["completed_attempt_count"])

    def test_one_completed_attempt_is_below_frozen_minimum_replication(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "in" / "telemetry.json"
            source.parent.mkdir()
            source.write_text(json.dumps([self.record()]), encoding="utf-8")

            IMPORTER.import_measurements(
                source.parent, root / "out", self.case_dirs, "2026-07-14T08:00:00Z"
            )
            report = json.loads(
                (root / "out" / "measurement_validation_report.json").read_text(
                    encoding="utf-8"
                )
            )

            self.assertEqual(3, report["minimum_completed_attempts_per_action"])
            self.assertEqual(0, report["covered_action_count"])
            self.assertIn(
                "insufficient_completed_attempt_replication",
                report["blocking_reasons"],
            )

    def test_tampered_source_fails_replayable_provenance(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "in" / "telemetry.jsonl"
            source.parent.mkdir()
            source.write_text(json.dumps(self.record()) + "\n", encoding="utf-8")
            IMPORTER.import_measurements(
                source.parent, root / "out", self.case_dirs, "2026-07-14T08:00:00Z"
            )
            source.write_text("{}\n", encoding="utf-8")

            report = VALIDATOR.validate_batch(
                root / "out" / "operational_cost_measurements.json",
                self.case_dirs,
            )

            self.assertFalse(report["provenance_valid"])
            self.assertTrue(
                any("source file sha256 mismatch" in error for error in report["semantic_errors"])
            )


if __name__ == "__main__":
    unittest.main()
